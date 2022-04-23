"""pro URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,re_path
from movie import views
from movie import knowledge_graph

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('init_neo4j/', knowledge_graph.init_neo4j),   # 知识图谱数据初始化


    path('login/', views.login,name='login'),   # 登录
    path('register/', views.register,name='register'),   # 注册

    path('index/', views.index,name='index'),   # 首页

    path('detail/<int:movie_id>/', views.detail,name='detail'),   # 详情页面
    path('collect/', views.collect),   # 收藏
    path('collect/del/', views.collect_del),   # 取消收藏
    path('score/', views.score),   # 评分
    path('all/comment/<int:movie_id>/', views.all_comment,name='all_comment'),   # 所有评论

    path('tages/movie/', views.tages_movie,name='tages_movie'),   # 分类浏览
    path('new/movie/<int:tip>/', views.new_movie,name='new_movie'),   # 最新上映
    path('search/movie/', views.search_movie,name='search_movie'),   # 影片搜索
    path('rec/movie/', views.rec_movie,name='rec_movie'),   # 电影推荐

    path('user/info/', views.user_info,name='user_info'),   # 个人中心
    path('user/comment/', views.user_comment,name='user_comment'),   # 我的评论
    path('user/collect/', views.user_collect,name='user_collect'),   # 我的收藏
    path('user/history/', views.user_history,name='user_history'),   # 观看历史

    # ------------------ 管理员 ---------------------- #
    path('admin/login/', views.admin_login,name='admin_login'),   # 管理员 登录

    path('admin/movie/', views.admin_movie,name='admin_movie'),   # 电影管理
    path('admin/movie/add/', views.admin_movie_add,name='admin_movie_add'),   # 电影管理 - 添加电影
    path('admin/movie/edit/<int:movie_id>', views.admin_movie_edit,name='admin_movie_edit'),   # 电影管理 - 编辑电影
    path('admin/movie/del/', views.admin_movie_del,name='admin_movie_del'),   # 电影管理 - 删除电影

    path('admin/user/', views.admin_user, name='admin_user'),  # 用户管理
    path('admin/user/add/', views.admin_user_add,name='admin_user_add'),   # 用户管理 - 添加用户
    path('admin/user/edit/<int:user_id>/', views.admin_user_edit,name='admin_user_edit'),   # 用户管理  - 编辑
    path('admin/user/del/', views.admin_user_del,name='admin_user_del'),   # 用户管理 - 删除用户

    path('admin/data/', views.admin_data, name='admin_data'),  # 数据统计
    path('admin/role/', views.admin_role, name='admin_role'),  # 角色管理
    path('admin/role/add/', views.admin_role_add, name='admin_role_add'),  # 角色管理 - 添加
    path('admin/role/del/', views.admin_role_del,name='admin_role_del'),   # 角色管理 - 删除


]
