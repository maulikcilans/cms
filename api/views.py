from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.exceptions import PermissionDenied
from .serializers import UserSerializer, ArticleSerializer, CommentSerializer
from .models import User, Article, Comment
from .permissions import IsAdmin, IsAuthorOrAdmin, IsCommenterOrAdmin
from rest_framework.filters import SearchFilter, OrderingFilter


# Create your views here.


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all().order_by("email")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]


class ArticleListView(generics.ListCreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "body"]
    ordering_fields = ["created_at", "updated_at"]

    def perform_create(self, serializer):
        if self.request.user.role not in ["admin", "author"]:
            raise PermissionDenied("You don't have permission to create an article.")

        is_published = self.request.data.get("is_published", False)
    
        if isinstance(is_published, str):
            is_published = is_published.lower() == "true"
    


        if self.request.user.role == "author" and is_published:
            raise PermissionDenied("Authors cannot publish articles directly.")

class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrAdmin]

    def perform_update(self, serializer):

        if self.request.user.role == "author" and self.request.user != serializer.instance.author:
                raise PermissionDenied("Authors can only edit their own articles.")

        
        if "is_published" in self.request.data and self.request.user.role != "admin":

            raise PermissionDenied("Only admins can publish/unpublish articles.")

    
        serializer.save()
    def perform_destroy(self, instance):
        if self.request.user.role == "author":
            raise PermissionDenied("Authors are not allowed to delete articles.")
        instance.delete()


class CommentListView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer

    def get_queryset(self):
        return Comment.objects.filter(article_id=self.kwargs["article_id"])

    def perform_create(self, serializer):
        serializer.save(
            commenter=self.request.user, article_id=self.kwargs["article_id"]
        )


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommenterOrAdmin]

    def perform_destroy(self, instance):
    
        if self.request.user != instance.commenter and self.request.user.role != 'admin':
            raise PermissionDenied("Only the commenter or an admin can delete this comment.")
        instance.delete()
