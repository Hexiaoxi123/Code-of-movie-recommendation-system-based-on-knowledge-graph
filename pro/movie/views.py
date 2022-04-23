from django.shortcuts import render, redirect,HttpResponse
from movie import models
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from movie import sentiment_analysis   # 调用情感分析
from py2neo import Graph, Node, Relationship, NodeMatcher,RelationshipMatcher
from py2neo.data import walk,Walkable

# 分页
def movies_paginator(movies, page):
    paginator = Paginator(movies,10)
    if page is None:
        page = 1
    movies = paginator.page(page)
    return movies



# 登录
def login(request):
    if request.method == "GET":
        return render(request, "login.html") # 进入到登录界面
    else:
        # form 表单验证
        # 1、获取提交的账号和密码
        account = request.POST.get('account')    # 获取前端用户填写的账号信息
        password = request.POST.get('password')

        # 2、检验用户是否合法
        obj = models.User.objects.filter(account=account, password=password).first()

        if not obj:
            return HttpResponse('用户名或密码错误！')

        # 3、获取用户信息和权限信息写入session
        request.session['user_info'] = {'id': obj.id, 'account': obj.account}
        # print(request.session['user_info'])

        return HttpResponse('ok')


# 注册功能
def register(request):
    if request.method == "GET":
        return render(request, "register.html")  # 表单验证失败返回一个空表单到注册页面
    else:
        account = request.POST.get('account')
        password = request.POST.get('password')
        email = request.POST.get('email')

        # 检验用户是否已经存在
        obj = models.User.objects.filter(account=account).first()

        if obj:
            return HttpResponse('该用户已存在！')
        else:
            # 将用户信息存入数据库
            models.User.objects.create(account=account, password=password, email=email)
            return HttpResponse('ok')


# 首页
def index(request):
    order = request.POST.get("order") or request.session.get('order')  # 排序规则
    request.session['order'] = order
    print(request.session['order'])

    if order == 'collect':
        movies = models.Movie.objects.annotate(collectors=Count('collect')).order_by('-collectors')[:10]
        print(movies.query)
        title = '收藏排序'
    elif order == 'rate':
        movies = models.Movie.objects.order_by('-d_rate')[:10]
        title = '评分排序'
    elif order == 'years':
        movies = models.Movie.objects.order_by('-years')[:10]
        title = '时间排序'
    else:
        movies = models.Movie.objects.order_by('-num')[:10]  # 获取前10个数据
        title = '流量排序'


    page_num = request.GET.get("page", 1)   # 获取页面
    movies = movies_paginator(movies, page_num)   # 分页展示
    return render(request, 'index.html', {'movies': movies,"title":title})


# 详情页面
def detail(request,movie_id):
    # movies = models.Movie.objects.filter(id = movie_id).values() # 获取电影详情
    movie = models.Movie.objects.get(id = movie_id)  # 获取电影详情

    # print(movie[0])
    movie.num += 1   # 增加电影的浏览量
    movie.save()

    rates = models.Rate.objects.filter(movie=movie).all().values("user__account",
                                                                 "comment","create_time")[:10]  # 获取当前电影所有的评论
    # print('121212',rates)

    user_id = request.session.get("user_info")['id']  # 获取当前用户id
    if user_id is not None:
        user_rate = models.Rate.objects.filter(movie=movie, user_id=user_id).first() # 获取当前用户的评分
        print(user_rate)
        # user = models.User.objects.get(pk=user_id)
        is_collect = movie.collect.filter(id=user_id).first()  # 判断是否有收藏

    return render(request, 'movieDetail.html', locals())


# 点击收藏
def collect(request):
    movie_id = request.POST.get('id')  # 接收前端收藏的电影id
    print(movie_id)
    print(type(movie_id))
    user = models.User.objects.get(id=request.session.get("user_info")['id']) # 获取当前用户对象
    movie = models.Movie.objects.get(id=movie_id)  # 获取电影对象
    movie.collect.add(user)  # 添加收藏
    movie.save()
    return HttpResponse('ok')


# 取消收藏
def collect_del(request):
    movie_id = request.POST.get('id')  # 电影id
    user_id = request.session.get("user_info")['id']    # 用户id
    # models.Movie.objects.filter(user_id=user_id, movie_id=movie_id).delete()

    movie = models. Movie.objects.get(id=movie_id)
    movie.collect.remove(user_id)  # 移除收藏信息

    movie.save()
    return HttpResponse('ok')


# 评分
def score(request):
    movie_id = request.POST.get('id')  # 电影id
    score = int(request.POST.get('score'))  # 评分
    comment = request.POST.get('comment')  # 评价

    user_id = request.session.get("user_info")['id']    # 用户id
    # print(user_id)

    # 对评论进行情感分析，并判断得分是否合理
    print(comment)
    print(score)
    emotional_value = sentiment_analysis.sentiment(comment)
    # emotional_value = [{'label': 'positive (stars 4 and 5)', 'score': 0.6958548426628113}]
    evalue = emotional_value[0]['label'][:8]
    print(evalue)
    if score < 5 and evalue=='positive':
        print("请重新输入评分！")
        return HttpResponse('请重新输入评分！')
    elif score >= 5 and evalue=='positive':
        print("正确")
    elif score >= 5 and evalue=="negative":
        print("请重新输入评分！")
        return HttpResponse('请重新输入评分！')
    elif score < 5 and evalue=="negative":
         print("正确")

    #  添加数据
    models.Rate.objects.create(movie_id = int(movie_id),user_id=int(user_id), mark=float(score), comment=comment)
    return HttpResponse('ok')


# 所有评论
def all_comment(request,movie_id):
    movie = models.Movie.objects.get(id=movie_id)  # 获取电影
    rates = models.Rate.objects.filter(movie=movie).all().values("user__account",
                                                                 "comment", "create_time")  # 获取当前电影所有的评论

    page_num = request.GET.get("page", 1)
    comment = movies_paginator(rates, page_num)  # 分页展示
    return render(request, 'allComment.html',{"comment":comment})


# 分类浏览
def tages_movie(request):

    type = request.GET.get("type") or request.session.get('type')  # 类型
    request.session['type'] = type

    print(request.session['type'])

    region = request.GET.get("region") or request.session.get('region')  # 地区
    request.session['region'] = region
    # print(request.session['region'])
    if region is None or region == '全部':
        region = ''

    if type is None or type == '全部':
        type = ''

    # if region is not None or type is not None:
    movies = models.Movie.objects.filter(
        Q(country__icontains=region) & Q(tags__name__icontains=type)
    )[:100]  # 进行内容的模糊搜索
    print(region)
    print(type)
    print(movies)
    # else:
    #     movies = models.Movie.objects.order_by('?')[:100]  # 随机展示电影数据


    tags = models.Tags.objects.all()  # 获取所有分类
    page_num = request.GET.get("page", 1)  # 获取页面
    movies = movies_paginator(movies, page_num)  # 分页展示
    return render(request, "tagesMovie.html", {'movies': movies,"tags":tags,'region':region,'type':type})



# 最新上映
def new_movie(request,tip):
    # 正在上映
    if tip == 0:
        # movies = models.NewMovie.objects.all().values()  # 获取正在上映电影数据
        # print(movies)
        movies = models.NewMovie.objects.exclude(d_rate='')  # 获取正在上映电影数据
        print(movies)
    # 即将上映
    if tip == 1:
        movies = models.NewMovie.objects.filter(d_rate='') # 获取即将上映电影数据
        print(movies)

    page_num = request.GET.get("page", 1)  # 获取页面
    movies = movies_paginator(movies, page_num)  # 分页展示
    print(tip)
    print(type(tip))
    return render(request, "newMovie.html", {'movies': movies,'tip':tip})


# 影片搜索
def search_movie(request):
    if request.method == "GET":
        key = request.session.get("search")  # 得到关键词
        print(key)
        return render(request, "searchMovie.html",{'state':'hidden'})
    else:
        key = request.POST["search"]    # 获取前端用户搜索的关键词
        request.session["search"] = key  # 记录搜索关键词解决跳页问题
        print(key)

        movies = models.Movie.objects.filter(
            Q(name__icontains=key) | Q(leader__icontains=key) | Q(director__icontains=key)
        )[:10]  # 进行内容的模糊搜索

        print(movies)
        if movies:
            state = 'hidden'
        else:
            state = ''

        return render(request, "searchMovie.html",{"movies": movies, 'title': key})


# 电影推荐
def rec_movie(request,):
    if request.method == "GET":
        # rec = knowledge_graph_recommend(5)

        user = models.User.objects.get(id=request.session.get("user_info")['id']) # 获取当前用户对象
        collect_id_ = user.movie_set.all().values('id')  # 反向查询 收藏的电影id

        if not collect_id_:
            return render(request, "recMovie.html", {"msg": "无历史数据无法推荐！"})

        all_rec_ids = []  # 收藏的电影id 列表
        for item in collect_id_:
            collect_id = item['id'] #获取用户收藏电影ID
            rec_ids = knowledge_graph_recommend(collect_id)#获取每个收藏电影相关电影，top k推荐
            all_rec_ids.extend(rec_ids)
        final_rec_ids = list(set(all_rec_ids))
        movies = models.Movie.objects.filter(id__in = final_rec_ids)[:10]#选择前10个显示，每个收藏电影会获得相似度排名前5的电影推荐，top k推荐中的k为5。
        print(movies)
        return render(request, "recMovie.html",{"movies":movies})



# 基于知识图谱和协同过滤算法的电影推荐
def knowledge_graph_recommend(recommend_id, k=5):
    # 连接neo4j数据库，输入地址、用户名、密码
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "123456"))
    #    graph.delete_all() #清除neo4j中原有的结点等所有信息
    nodeMatcher = NodeMatcher(graph)
    is_node = nodeMatcher.match('电影推荐').first()
    #    print(is_node)
    if not is_node:

        graph.run('''LOAD CSV WITH HEADERS  FROM 'file:///movies.csv' AS row
                  MERGE (ny:电影推荐{name:row.title,id:row.movie_id})''')
        graph.run('''LOAD CSV WITH HEADERS FROM 'file:///movies_sims_entity.csv' AS row
                      match (from:电影推荐{id:row.sid}),(to:电影推荐{id:row.eid})
                      merge (from)-[r:相似{相似度:row.sim}]->(to)'''
                  )
    else:
        print("已存在！")
    result = nodeMatcher.match('电影推荐').where(id=str(recommend_id))
    find_node = list(result)[0]  # 根据节点id找到整个节点
    relMatcher = RelationshipMatcher(graph)  #
    relResult = relMatcher.match([find_node], r_type='相似').order_by("_.相似度")  # 找到存在'相似'关系的路径，然后找到对应节点
    recommend_result = []
    for rel in list(relResult):
        temp = []
        for w in walk(rel):
            temp.append(w)
        rel_id = temp[2]['id']  # 知识图谱关系
        recommend_result.append(rel_id)
    recommend_result = reversed([int(rec) for rec in recommend_result])
    final_recommend_result = list(filter(lambda x: x != recommend_id, recommend_result))[:k]  # 去除自身id,得到关联ID
    return final_recommend_result


 # 个人中心
def user_info(request):
    if request.method == "GET":
        user_id = request.session.get("user_info")['id']  # 用户id
        user_info = models.User.objects.filter(id=user_id).values()  # 获取用户的信息
        print(user_info)
        return render(request, "userInfo.html", {"user_info": user_info[0]})
    else:
        account = request.POST.get('account')
        password = request.POST.get('password')
        email = request.POST.get('email')
        id = request.POST.get('id')

        # 修改用户信息
        models.User.objects.filter(id=id).update(account=account, password=password, email=email)
        return HttpResponse('ok')


# 我的评论
def user_comment(request):
    if request.method == "GET":
        user_id = request.session.get("user_info")['id']  # 用户id
        obj_info = models.Rate.objects.filter(user_id=user_id).values("id",'movie__name',
                                                                      'mark','comment', 'create_time')
        return render(request, "userComment.html",{"obj_info":obj_info})
    else:
        # ------ 删除评论 ------ #
        id = request.POST.get('id')  # 接收删除的id

        # 删除操作
        models.Rate.objects.filter(id=id).delete()
        return HttpResponse('ok')


# 我的收藏
def user_collect(request):
    if request.method == "GET":
        user_id = request.session.get("user_info")['id']  # 用户id

        # 查询我收藏电影的所有信息
        first = models.User.objects.filter(id=user_id).first()
        obj_info = first.movie_set.all()  # 反向查询 收藏的电影
        # print(info)
        for i in obj_info:
            print(i)

        return render(request, "userCollect.html", {"obj_info": obj_info})
        # return render(request, "userCollect.html")
    else:
        # ------ 删除收藏 ------ #
        movie = models.Movie.objects.get(id=request.POST.get('id'))
        user = models.User.objects.get(id=request.session.get("user_info")['id'])
        movie.collect.remove(user)

        # 删除操作
        # models.Rate.objects.filter(id=id).delete()
        return HttpResponse('ok')


# 观看历史
def user_history(request):
    if request.method == "GET":
        return render(request, "userInfo.html")


# ------------------------ 管理员端 ----------------------------- #
# 管理员 登录
def admin_login(request):
    if request.method == "GET":
        return render(request, "adminLogin.html")
    else:
        # 1、获取提交的账号和密码
        account = request.POST.get('account')
        password = request.POST.get('password')

        # 2、检验用户是否合法
        obj = models.AdminInfo.objects.filter(account=account, password=password).first()
        if not obj:
            return HttpResponse('用户名或密码错误！')

        request.session['user_info'] = {'id': obj.id, 'account': obj.account,'identity': obj.identity}
        print(request.session['user_info']['identity'])
        # ------------------------- 权限管理 --------------------------------- #
        permission_queryset = obj.permissions.all().values('title','url','icon') # 获取该用户的权限

        menu_list = []  # 可以成为菜单的权限以 菜单的名称、图标

        for row in permission_queryset:
            menu_list.append(
                {'title': row['title'], 'icon': row['icon'],'url': row['url']})

        request.session['menu_list'] = menu_list  # 将菜单放到session中
        # [{'title': '电影管理', 'icon': 'glyphicon glyphicon-tasks', 'url': '/admin/movie/'}]#}

        print(menu_list)
        return HttpResponse('ok')
        # ---------------------------------------------------------- #
        #
        # # 2、检验用户是否合法
        # if account == 'admin' and password == '123456':
        #     # 3、获取用户信息和权限信息写入session
        #     request.session['user_info'] = {'account': account}
        #     # print(request.session['user_info'])
        #
        #     return HttpResponse('ok')
        # else:
        #     return HttpResponse('用户名或密码错误！')


# from functools import wraps
# def dec(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         request = args[0]
#         request.session['current_url'] = reverse("admin_movie")
#         # is_login = request.session.get("login_in")
#         func(*args, **kwargs)
#
#     return wrapper




# 电影管理
# @dec
def admin_movie(request):
    if request.method == "GET":
        request.session['current_url'] = reverse("admin_movie")
        movies = models.Movie.objects.all()[:500]  # 获取电影数据

    else:
        keyWord = request.POST.get('keyWord')
        movies = models.Movie.objects.filter(
            Q(name__icontains=keyWord) | Q(leader__icontains=keyWord) | Q(director__icontains=keyWord)
        )[:10]  # 进行内容的模糊搜索

    page_num = request.GET.get("page", 1)  # 获取页面
    movies = movies_paginator(movies, page_num)  # 分页展示
    return render(request, "adminMovie.html", {'movies': movies})


# 电影管理 - 添加电影
def admin_movie_add(request):
    if request.method == "GET":
        # 获取所有标签
        tags = models.Tags.objects.all()
        return render(request, "adminMovieAdd.html",{"tags":tags})
    else:
        name = request.POST.get('name')
        director = request.POST.get('director')
        country = request.POST.get('country')
        years = request.POST.get('years')
        leader = request.POST.get('leader')
        intro = request.POST.get('intro')
        tags_ = request.POST.getlist('tags')

        tags = [int(i) for i in tags_]   # 标签id
        print(tags)

        file_obj = request.FILES.get("image_link")  # 获取到前端提交的图片

        # 将文件存入到本地目录data中， file_obj.name是要上传文件的文件名
        with open('static/images/movie_cover/' + file_obj.name, "wb") as f:
            for data in file_obj.chunks():
                f.write(data)

        # 将信息存入数据库
        movie = models.Movie.objects.create(name=name, director=director, country=country,years=years
                                    ,leader=leader,intro=intro,image_link='movie_cover/'+file_obj.name,num=0,d_rate_nums=0,d_rate=None)

        bs = models.Tags.objects.filter(id__in=tags)  # 获取对应id 的标签
        movie.tags.add(*bs)

        # 获取所有标签
        tags = models.Tags.objects.all()

        return render(request, "adminMovieAdd.html", {"msg": '添加成功！',"tags":tags})


# 电影管理 - 编辑电影
def admin_movie_edit(request,movie_id):
    if request.method == "GET":
        movie = models.Movie.objects.get(id=movie_id)  # 获取电影详情
        tags_list_ = movie.tags.all()  # 获取该电影所有的标签

        tags_list = []
        # print(tags_list)
        for i in tags_list_:
            tags_list.append(i.id)
        print(tags_list)
        # 获取所有标签
        tags = models.Tags.objects.all()
        return render(request, "adminMovieEdit.html", {"movie":movie,"tags_list":tags_list,"tags":tags})
    else:
        name = request.POST.get('name')
        director = request.POST.get('director')
        country = request.POST.get('country')
        years = request.POST.get('years')
        leader = request.POST.get('leader')
        intro = request.POST.get('intro')
        new_tags_ = request.POST.getlist('tags')

        new_tags = [int(i) for i in new_tags_]  # 标签id -- 转化为列表
        print(new_tags)

        file_obj = request.FILES.get("image_link")  # 获取到前端提交的图片

        # 如果有上传新的图片
        if file_obj:

            # 将文件存入到本地目录data中， file_obj.name是要上传文件的文件名
            with open('static/images/movie_cover/' + file_obj.name, "wb") as f:
                for data in file_obj.chunks():
                    f.write(data)

            #  更新数据库
            models.Movie.objects.filter(id=movie_id).update(name=name, director=director, country=country,
                                                              years=years , leader=leader, intro=intro,
                                                            image_link='movie_cover/'+file_obj.name )
        else:
            #  更新数据库
            models.Movie.objects.filter(id=movie_id).update(name=name, director=director, country=country,
                                                            years=years, leader=leader, intro=intro)

        movie_ = models.Movie.objects.get(id=movie_id)  # 获取电影对象
        movie_.tags.set(new_tags)  # 更新标签


        # 获取所有标签
        tags = models.Tags.objects.all()
        movie = models.Movie.objects.get(id=movie_id)  # 获取电影详情

        return render(request, "adminMovieEdit.html", {"msg": '编辑成功！', "tags": tags, "movie": movie,'tags_list':new_tags})


#  电影管理 - 删除电影
def admin_movie_del(request):
    id = request.POST.get('id')
    models.Movie.objects.filter(id=id).delete()
    return HttpResponse('ok')


 # 用户管理
def admin_user(request):
    if request.method == "GET":
        request.session['current_url'] = reverse("admin_user")

        users = models.User.objects.all() # 获取用户数据
        return render(request, "adminUser.html",{"users":users})
    else:
        keyWord = request.POST.get('keyWord')
        users = models.User.objects.filter(
            Q(account__icontains=keyWord) | Q(email__icontains=keyWord)
        ) # 进行内容的模糊搜索
        return render(request, "adminUser.html", {"users": users})


#  用户管理 - 添加用户
def admin_user_add(request):
    if request.method == "GET":
        return render(request, "adminUserAdd.html")
    else:
        account = request.POST.get('account')
        password = request.POST.get('password')
        email = request.POST.get('email')

        # 将信息存入数据库
        models.User.objects.create(account=account, password=password, email=email)
        return render(request, "adminUserAdd.html", {"msg": '添加成功！'})


# 用户管理  - 编辑
def admin_user_edit(request,user_id):
    if request.method == "GET":

        user = models.User.objects.filter(id=user_id)  # 获取用户详情
        return render(request, "adminUserEdit.html", {"user":user[0]})
    else:
        print(user_id)
        id = request.POST.get('id')
        account = request.POST.get('account')
        password = request.POST.get('password')
        email = request.POST.get('email')
        print(id)
        # 修改用户信息
        models.User.objects.filter(id=id).update(account=account, password=password, email=email)

        return HttpResponse('ok')


#  用户管理 - 删除用户
def admin_user_del(request):
    id = request.POST.get('id')
    models.User.objects.filter(id=id).delete()
    return HttpResponse('ok')


# 数据统计
def admin_data(request):
    if request.method == "GET":
        request.session['current_url'] = reverse("admin_data")

        user_sum = models.User.objects.all().count()  # 注册用户数量
        movie_sum = models.Movie.objects.all().count()  # 电影总数量
        tag_sum = models.Tags.objects.all().count()  # 电影种类数量

        # 评分最高T10电影
        rate_movies = models.Movie.objects.all().values("name","d_rate").order_by('-d_rate')[0:10]
        # print(rate_movies)

        rate_x = []
        rate_y = []
        for item in rate_movies:
            rate_x.append(item['name'])
            rate_y.append(item['d_rate'])

        # 最受欢迎T10电影
        view_movies = models.Movie.objects.all().values("name", "num").order_by('-num')[0:10]

        view_x = []
        view_y = []
        for item in view_movies:
            view_x.append(item['name'])
            view_y.append(item['num'])


        return render(request, "adminData.html",{"user_sum":user_sum,"movie_sum":movie_sum,"tag_sum":tag_sum,
                                                 "rate_x":rate_x,'rate_y':rate_y,
                                                 "view_x": view_x, 'view_y': view_y})


# 角色管理
def admin_role(request):
    if request.method == "GET":
        request.session['current_url'] = reverse("admin_role")

        user = models.AdminInfo.objects.all()  # 获取管理员信息

        """
      [{'id': 1, 'account': 'admin', 'password': 'admin', 'identity': '超级管理员', 'permissions__title': '电影管理', 'created_time': datetime.datetime(2022, 4, 17, 13, 17, 2, 440829, tzinfo=<UTC>)},
       {'id': 1, 'account': 'admin', 'password': 'admin', 'identity': '超级管理员', 'permissions__title': '用户管理', 'created_time': datetime.datetime(2022, 4, 17, 13, 17, 2, 440829, tzinfo=<UTC>)}, 
       {'id': 1, 'account': 'admin', 'password': 'admin', 'identity': '超级管理员', 'permissions__title': '数据统计', 'created_time': datetime.datetime(2022, 4, 17, 13, 17, 2, 440829, tzinfo=<UTC>)}, 
       {'id': 1, 'account': 'admin', 'password': 'admin', 'identity': '超级管理员', 'permissions__title': '角色管理', 'created_time': datetime.datetime(2022, 4, 17, 13, 17, 2, 440829, tzinfo=<UTC>)}]>
        
        """
        return render(request, "adminRole.html", locals())


#  角色管理 - 添加
def admin_role_add(request):
    if request.method == "GET":
        return render(request, "adminRoleAdd.html")
    else:
        account = request.POST.get('account')
        password = request.POST.get('password')
        permissions_ = request.POST.getlist('permissions')

        # 检验用户是否已经存在
        obj = models.AdminInfo.objects.filter(account=account).first()

        if obj:
            return render(request, "adminRoleAdd.html", {"msg": '该用户已存在！'})

        else:
            permissions = [int(i) for i in permissions_]  # 权限id
            print(permissions)

            # 将信息存入数据库
            admin = models.AdminInfo.objects.create(account=account, password=password,identity='普通管理员')
            bs = models.Permission.objects.filter(id__in=permissions)
            admin.permissions.add(*bs)
            return render(request, "adminRoleAdd.html", {"msg": '添加成功！'})


#   角色管理 - 删除
def admin_role_del(request):
    id = request.POST.get('id')
    # 检查是否为超级管理员，超级管理员不能被删除
    identity = models.AdminInfo.objects.filter(id=id).values("identity")
    print('身份为',identity[0]['identity'])

    if identity[0]['identity'] == '超级管理员':
        return HttpResponse('此账号为超级管理员，您无法删除！')

    models.AdminInfo.objects.filter(id=id).delete()
    return HttpResponse('ok')