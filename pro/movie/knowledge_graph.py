# -*- coding: utf-8 -*-
from django.shortcuts import render,HttpResponse,redirect
import os
import pandas as pd
from py2neo import Node, Graph, Relationship
from py2neo import NodeMatcher
import jieba.posseg as pseg
from gensim import corpora, models, similarities

#导入停用词
def get_stop_words(path = 'data/stop_words_ch.txt'):
    stopwords = open(path,'r',encoding='utf-8').readlines()
    stopwords = [ w.strip() for w in stopwords ]
    return stopwords    
#对电影的简介内容分词、去停用词
def tokenization(text):
    stop_words = get_stop_words()+['丨']
    # 过滤掉一些不可用的词性 按照次序,分别为 连词，副词，方位词，数词，介词，代词，时间词，助词，过，字符串
    stop_flag = ['x', 'c', 'u','d', 'p', 't', 'uj', 'm', 'f', 'r']
    result = []
    words = pseg.cut(text)#分词
    for word, flag in words:
        if flag not in stop_flag and word not in stop_words:
            result.append(word)
    return result


# 得到文本内容的词典模型和tfidf词向量索引
def get_tfidf(path):
    movies = pd.read_excel(path)
    data_in = movies[['序号','简介']]
    data_cut_words = data_in['简介'].apply(lambda x:tokenization(x))   # 分词
    data_corpus = data_cut_words.values     # 获得分词列表
    dictionary = corpora.Dictionary(data_corpus)    # 用来构造词典
    doc_vectors = [dictionary.doc2bow(text) for text in data_corpus]    # 计算得到词向量，每一条原始数据向量化
    tfidf = models.TfidfModel(doc_vectors)      # Tfidf模型，使用数字语料生成TFIDF模型
    tfidf_vectors = tfidf[doc_vectors]      # Tfidf向量，把全部语料向量化成TFIDF模式，这个tfidfModel可以传入二维数组
    similarity = similarities.MatrixSimilarity(tfidf_vectors)    # 建立索引
    similarity.num_best = 6#获得相似排名前6的相似度，包含自己本身
    return dictionary,similarity,data_in,doc_vectors


# 构建电影相似度三元实体
def get_recommend_entity(o_path='data/movie_movie.xlsx',t_path='data/movies_sims_entity.csv'):
    dictionary,similarity,data_index,doc_vectors = get_tfidf(o_path)
    if not os.path.exists(t_path):
        ternary_data = []
        for i in range(len(data_index)):
            sims = similarity[doc_vectors[i]]
            for j,sim in sims:
                if i==j:#去除自己本身的相似结果
                    continue
                rid_i = data_index['序号'][i]
                rid_j = data_index['序号'][j]
                rij_sim = sim
                ternary_data.append([rid_i,rij_sim,rid_j])
            print("第{}已经处理完毕!".format(i))
        ternary_data_df = pd.DataFrame(ternary_data,columns=['sid','sim','eid'])#数据有三列，列名分别为'sid','eid','sim'
        ternary_data_df.to_csv(t_path,index=False)
    else:
        ternary_data_df = pd.read_csv(t_path)
    return ternary_data_df
#获取电影数据的三元组
def get_movie_triples(o_path='data/movie_movie.xlsx',t_path='data/movie_triples.xlsx'):
    
    movies = pd.read_excel(o_path)
    movies['上映日期'] = movies['上映日期'].apply(lambda x : x.strftime('%Y-%m-%d'))
    del movies['豆瓣图片地址']
    if not os.path.exists(t_path):
        relations = ['导演','地区','上映日期','主演','评分','语言','标签','片长']
        triple_list = []
        for mid in movies['电影名']:
            for relation in relations:
                entity1 = movies[movies['电影名']==mid]['电影名'].values[0]
                entity2 = movies[movies['电影名']==mid][relation].values[0]
                if isinstance(entity2,str):
                    if '/' in entity2:
                        for e2 in entity2.split('/'):
                            triple_list.append([entity1,relation,e2])
                    else:
                            triple_list.append([entity1,relation,entity2])
                else:
                    triple_list.append([entity1,relation,entity2])
        
        triple_df = pd.DataFrame(triple_list,columns=['entity1','relation','entity2'])
        triple_df.to_excel(t_path,index=False)
    else:
        triple_df = pd.read_excel(t_path)
    return triple_df
#创建知识图谱
def create_knowledge_graph():
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "1451850044"))
    
    movie_triples = get_movie_triples()
    for index,row in movie_triples.iterrows():
        print('正在插入数据！')
        e1 = row.tolist()[0]
        e2 = row.tolist()[2]
        r = row.tolist()[1]
        start_node = graph.nodes.match("电影", name=e1).first()
        end_node = graph.nodes.match("属性", name=e2).first()
        if start_node and end_node:
            relation=Relationship(start_node,r,end_node)
            graph.merge(start_node,"电影","name")
            graph.merge(end_node,"属性","name")   
            graph.merge(relation,'电影','属性')
        else:
            start_node=Node("电影",name=e1)
            end_node=Node("属性",name=e2)
            relation=Relationship(start_node,r,end_node)
            graph.merge(start_node,"电影","name")
            graph.merge(end_node,"属性","name")   
            graph.merge(relation,'电影','属性')
            
def init_neo4j(request):
    """
    初始化neo4j中的数据
    """
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "1451850044"))
    print("开始插入数据")
    graph.delete_all()  # 清除neo4j中原有的结点等所有信息
    print("neo4j清除完毕")
    node_matcher = NodeMatcher(graph)
    node = node_matcher.match("电影").first()
    if not node:
        create_knowledge_graph()
    return HttpResponse('neo4j数据加载完成！')
        
    
    


