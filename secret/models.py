from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from .utils.encryption import encrypt

class Tag(models.Model):
    name = models.CharField(verbose_name='名称', max_length=20)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = verbose_name_plural = '标签'



class Secret(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, verbose_name='创建人')
    host = models.CharField(verbose_name='host', max_length=20)
    username = models.CharField(verbose_name='用户名', max_length=20, blank=True, null=True)
    secret = models.CharField(verbose_name='密码', max_length=255)
    tag = models.ForeignKey(Tag, to_field='id', verbose_name='标签', on_delete=models.PROTECT, blank=True, null=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    note = models.CharField(verbose_name='备注', max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.username}@{self.host}'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.secret = encrypt(self.secret).decode('utf-8')

        super(Secret, self).save(force_insert, force_update, using,
                                 update_fields)

    class Meta:
        verbose_name = verbose_name_plural = '密码记录'


class Permission(models.Model):
    host = models.ForeignKey(Secret, verbose_name='host', on_delete=models.CASCADE, blank=True, null=True,
                             related_name='pers')
    agree = models.BooleanField(verbose_name='是否同意', default=False)
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='申请人')
    reason = models.CharField(verbose_name='申请原因/用途', max_length=200, blank=True, null=True)
    create_time = models.DateTimeField(verbose_name='申请时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name='审批时间', blank=True, null=True)

    def __str__(self):
        show_per = self.host.host
        return f"{self.applicant.username}:{show_per}"

    class Meta:
        verbose_name = verbose_name_plural = '权限申请'
