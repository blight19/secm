from django.contrib import admin
from django.db.models import Q
from django import forms
from django.contrib import messages
from .models import Secret, Tag, Permission
from .utils.encryption import decrypt
from import_export.admin import ImportMixin
from import_export import resources


class SecretResource(resources.ModelResource):
    # 开启导入功能
    def __init__(self, owner):
        # 将owner_id传入 为当前访问人的id
        self.owner_id = owner
        super().__init__()

    def save_instance(self, instance, using_transactions=True, dry_run=False):
        if instance.id:
            try:
                obj = Secret.objects.get(pk=instance.id)
            # 查找是否存在这个id 存在则为更新 不存在则创建新的密码记录
            except Secret.DoesNotExist:
                instance.owner_id = self.owner_id
            # 存在 则判断所有者是否是本人
            else:
                if obj.owner.pk != self.owner_id:
                    raise PermissionError('无访问权限')

        else:
            instance.owner_id = self.owner_id
        super(SecretResource, self).save_instance(instance, using_transactions, dry_run)

    class Meta:
        model = Secret
        fields = ('id', 'host', 'username', 'secret', 'tag', 'note')


def decrypt_secret(value):
    # 用于用户自己查看的时候进行解密，显示明文密码
    if value is None:
        return None
    return decrypt(value.encode('utf-8'))


class SecretForm(forms.ModelForm):
    # 重写form 主要用于密码进行明文显示
    secret = forms.CharField(label='密码', required=False, )
    secret.prepare_value = decrypt_secret


@admin.register(Secret)
class SecretAdmin(ImportMixin, admin.ModelAdmin):
    # 列表页显示
    list_display = ['host', 'tag', 'create_time', 'owner_name', 'note']
    # 列表页筛选
    list_filter = ['tag', 'owner__first_name']
    # 添加的时候的Form
    form = SecretForm
    # 需要搜索的字段
    search_fields = ['host', 'note']
    # 导入时候的class
    resource_class = SecretResource

    # 重写方法 将ower放入参数中 方便resource_class使用
    def get_import_resource_kwargs(self, request, form=form, *args, **kwargs):
        return {'owner': request.user.pk}

    # 详情页的field
    def get_fields(self, request, obj=None):
        base = ['host', 'tag', 'note']
        # obj为空 则判断为添加 添加的时候任何人都可添加
        if obj is None:
            return base + ['username', 'secret']
        # 自己创建的有所有字段
        if request.user == obj.owner:
            return ['owner_name'] + base + ['username', 'secret']
        # 申请的并且已通过
        if obj.pers.filter(Q(agree=True) & Q(applicant=request.user)):
            return ['owner_name'] + base + ['username', 'secret_display']
        # 未申请通过 且不是创建人
        return []
    # 只读属性
    def get_readonly_fields(self, request, obj=None):
        # obj为空 则判断为添加 添加的时候无只读属性
        if obj is None:
            return []
        # 创建人自己访问的时候 不允许修改所有者
        if request.user == obj.owner:
            return ['owner', 'owner_name']
        # 非创建人访问的时候
        return []

    '''--------------------------------更改删除权限开始-------------------------------------------'''

    def has_view_permission(self, request, obj=None):
        if obj is None or request.user == obj.owner or obj.pers.filter(Q(agree=True) & Q(applicant=request.user)):
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if obj is None or request.user == obj.owner:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if obj is None or request.user == obj.owner:
            return True
        return False

    '''------------------------------------权限处理结束---------------------------'''

    '''-------------------------自定义字段开始-----------------------------------'''

    def secret_display(self, obj):
        return decrypt(obj.secret.encode('utf-8'))

    secret_display.short_description = '明文密码'

    def owner_name(self, obj):
        return obj.owner.first_name

    owner_name.short_description = '创建人'
    '''-------------------------自定义字段结束-----------------------------------'''

    def save_model(self, request, obj, form, change):
        obj.owner = request.user
        return super().save_model(request, obj, form, change)

    '''自定义actions'''
    actions = ['make_published']
    # 删除 “删除”动作
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']

        return actions
    #申请选中数据库动作
    def make_published(self, request, queryset):
        user = request.user
        perms = []
        for x in queryset:
            if x.owner != request.user:
                perms.append(Permission(applicant=user, host=x))
        Permission.objects.bulk_create(perms)

    make_published.short_description = "申请使用选中数据库"

    class Media:
        js=('secret_hidden.js',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'create_time']
    fields = ['name']
    actions_on_top = False
    actions = None

    def save_model(self, request, obj, form, change):
        obj.owner = request.user
        return super().save_model(request, obj, form, change)

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return False

# 权限申请页面的Form
class PermissionForm(forms.ModelForm):
    reason = forms.CharField(widget=forms.Textarea(attrs={'cols': '120', 'rows': '10'}), label='申请原因', required=False)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['host', 'applicant_display', 'owner_display', 'agree', 'create_time']
    fields = ['agree', 'reason']
    list_filter = ['applicant__first_name', 'agree', 'host__owner__first_name']
    form = PermissionForm

    def applicant_display(self, obj):
        return obj.applicant.first_name

    applicant_display.short_description = '申请人'

    def owner_display(self, obj):
        return obj.host.owner.first_name

    owner_display.short_description = '创建人'

    def get_readonly_fields(self, request, obj=None):

        if request.user == obj.host.owner:
            return ['host', 'applicant', 'reason']
        return ['agree']

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        qs = super(PermissionAdmin, self).get_queryset(request=request)

        return qs.filter(Q(host__owner=request.user) | Q(applicant=request.user))

    def has_view_or_change_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user == obj.host.owner or request.user == obj.applicant:
            return True
        return False

    '''自定义actions'''
    actions = ['make_agree']

    def make_agree(self, request, queryset):
        objs = []
        no_per = []
        for x in queryset:
            if x.host.owner == request.user:
                objs.append(x)
                x.agree = True
            else:
                no_per.append(x)

        Permission.objects.bulk_update(objs, ['agree', ])
        info_str = ''
        if not objs == []:
            info_str = f'{",".join([x.host.host for x in objs])}审核成功'
        if not no_per == []:
            info_str += f'{",".join([x.host.host for x in no_per])}审核失败'

        messages.info(request, info_str)

    make_agree.short_description = "批量通过"


admin.site.site_title = "DBA TEAM后台管理"
admin.site.site_header = "DBA TEAM"
