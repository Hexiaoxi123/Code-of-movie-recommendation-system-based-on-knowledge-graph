from django.db import models



# 数据库表
class User(models.Model):
    """
    用户信息表
    """
    account = models.CharField(max_length=255, unique=True, verbose_name="账号")
    password = models.CharField(max_length=255, verbose_name="密码")
    email = models.EmailField(verbose_name="邮箱")
    created_time = models.DateTimeField(auto_now_add=True)


class Tags(models.Model):
    """
    类别表
    """
    name = models.CharField(max_length=255, verbose_name="类别", unique=True)



class Movie(models.Model):
    """
    电影信息表
    """
    tags = models.ManyToManyField(Tags, verbose_name='类别', blank=True)    #多对多关系
    collect = models.ManyToManyField(User, verbose_name="收藏者", blank=True)
    name = models.CharField(verbose_name="电影名称", max_length=255)
    director = models.CharField(verbose_name="导演名称", max_length=255)
    country = models.CharField(verbose_name="地区", max_length=255)
    years = models.DateField(verbose_name='上映日期')
    leader = models.CharField(verbose_name="主演", max_length=1024)
    d_rate_nums = models.IntegerField(verbose_name="豆瓣评价数")
    d_rate = models.CharField(verbose_name="豆瓣评分", max_length=255,null=True)
    intro = models.TextField(verbose_name="描述")
    num = models.IntegerField(verbose_name="浏览量", default=0)
    origin_image_link = models.URLField(verbose_name='豆瓣图片地址', max_length=255, null=True)
    image_link = models.FileField(verbose_name="封面图片", max_length=255, upload_to='movie_cover')
    imdb_link = models.URLField(null=True)
    language = models.CharField(verbose_name="语言", max_length=500, null=True)
    label = models.TextField(verbose_name="标签")
    long = models.CharField(verbose_name="片长", max_length=255, null=True)



class Rate(models.Model):
    """
    评分表：用户对电影打分数据
    """
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, blank=True, null=True, verbose_name="电影id"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True, verbose_name="用户id",
    )
    mark = models.FloatField(verbose_name="评分")
    comment = models.TextField(verbose_name="评论内容",null=True)
    create_time = models.DateTimeField(verbose_name="发布时间", auto_now_add=True)



class NewMovie(models.Model):
    """
    新上映电影
    """
    name = models.CharField(verbose_name="电影名称", max_length=255, unique=True)
    years = models.CharField(verbose_name='上映年份', max_length=255)
    leader = models.TextField(verbose_name="主演")
    d_rate = models.CharField(verbose_name="评分", max_length=255)
    director = models.CharField(verbose_name="导演", max_length=255)
    type = models.CharField( verbose_name='类型', max_length=255)
    country = models.CharField(verbose_name="国家", max_length=255)
    intro = models.TextField(verbose_name="描述")
    image_link = models.URLField(verbose_name="封面图片", max_length=255, null=True)
    language = models.CharField(verbose_name="语言", max_length=500, null=True)
    long = models.CharField(verbose_name="片长", max_length=255, null=True)


class AdminInfo(models.Model):
    """
    管理员表
    """
    account = models.CharField(verbose_name='账号', max_length=32)
    password = models.CharField(verbose_name='密码', max_length=64)
    identity = models.CharField(verbose_name='身份', max_length=64,null=True)
    permissions = models.ManyToManyField(verbose_name='拥有的所有权限', to='Permission', blank=True)
    created_time = models.DateTimeField(auto_now_add=True,null=True)


class Permission(models.Model):
    """
    权限表
    """
    title = models.CharField(verbose_name='标题', max_length=32)
    url = models.CharField(verbose_name='含正则的URL', max_length=128)

    icon = models.CharField(max_length=32, null=True, blank=True)
    """
    null:如果为True，Django将在数据库中存储一个空值NULL。默认为 False。
    blank:如果为True，则允许该字段为空白。默认为False。

    注意，该项与null是不同的，null纯粹是与数据库相关的。而blank则与验证相关。如果一个字段设置为blank=True，
        表单验证时允许输入一个空值。而blank=False，则该项必需输入数据。

    """

