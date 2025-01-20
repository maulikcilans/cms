from rest_framework import serializers
from .models import User,Article,Comment

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['id','email','role','password']
        extra_kwargs={'password':{'write_only':True}}

    def create(self, validated_data):
        if validated_data['role'] not in ['admin', 'author', 'viewer']:
            raise serializers.ValidationError("Invalid role")
        user = User.objects.create_user(**validated_data)
        return user

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'
        read_only_fields = ['author', 'created_at', 'updated_at']

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['article','commenter', 'created_at']
       