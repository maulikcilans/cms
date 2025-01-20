from django.urls import path

from . import views
urlpatterns = [
    #User endpoints
    path('register/',views.RegisterView.as_view(),name='register'),
    path('users/',views.UserListView.as_view(),name="user-list"),

     # Article endpoints
    path('articles/', views.ArticleListView.as_view(), name='article-list'),
    path('articles/<int:pk>/',views.ArticleDetailView.as_view(), name='article-detail'),

    # Comment endpoints
    path('articles/<int:article_id>/comments/',views.CommentListView.as_view(), name='comment-list'),
    path('comments/<int:pk>/',views.CommentDetailView.as_view(), name='comment-detail'),

]
