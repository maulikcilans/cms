from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Article, Comment

User = get_user_model()

class APITestCases(APITestCase):
    def setUp(self):
        # Create users with different roles
        self.admin = User.objects.create_user(email="admin@test.com", password="admin123", role="admin")
        self.author = User.objects.create_user(email="author@test.com", password="author123", role="author")
        self.commenter = User.objects.create_user(email="commenter@test.com", password="commenter123", role="commenter")

        # Create a sample article and comment for testing
        self.article = Article.objects.create(
            title="Test Article",
            body="This is a test article.",
            author=self.author,
            is_published=False,
        )
        self.comment = Comment.objects.create(
            body="This is a test comment.",
            commenter=self.commenter,
            article=self.article,
        )

    def test_role_based_access_control(self):
        # Admin user should be able to access user list
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/users/")
       
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Author user should not be able to access user list
        self.client.force_authenticate(user=self.author)
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_create_article(self):
        # Author creates an article
        self.client.force_authenticate(user=self.author)
        print(self.author.role)
        data = {"title": "New Article", "body": "Content","is_published": False}
        response = self.client.post("/api/articles/", data)
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    

    def test_admin_create_article(self):
        # Admin creates an article
        self.client.force_authenticate(user=self.admin)
        data = {"title": "Admin Article", "body": "Content", "is_published": True}
        response = self.client.post("/api/articles/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_author_cannot_publish_article(self):
        # Author tries to create a published article
        self.client.force_authenticate(user=self.author)
        data = {"title": "New Article", "body": "Content", "is_published": True}
        response = self.client.post("/api/articles/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_crud_operations_for_articles(self):
        # GET article by ID (should be accessible)
        self.client.force_authenticate(user=self.author)
        response = self.client.get(f"/api/articles/{self.article.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Author can update the article
        self.client.force_authenticate(user=self.author)
        data = {"title": "Updated Title"}
        response = self.client.patch(f"/api/articles/{self.article.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Updated Title")

        # Author cannot delete the article
        response = self.client.delete(f"/api/articles/{self.article.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin can delete the article
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/articles/{self.article.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_comment_crud_operations(self):

        # Test: Commenter can create a comment
        self.client.force_authenticate(user=self.commenter)
        data = {"body": "This is a new comment."}
        response = self.client.post(f"/api/articles/{self.article.id}/comments/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment_id = response.data["id"]
        self.assertEqual(response.data["body"], data["body"])

        # Test: Author cannot update comment created by commenter (should get 403)
        self.client.force_authenticate(user=self.author)
        updated_data = {"body": "Updated by author."}
        response = self.client.put(f"/api/comments/{comment_id}/", updated_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test: Commenter can update their own comment
        self.client.force_authenticate(user=self.commenter)
        updated_data = {"body": "Updated comment content by commenter."}
        response = self.client.put(f"/api/comments/{comment_id}/", updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["body"], updated_data["body"])

    
        # Test: Admin can delete any comment
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/comments/{comment_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Ensure the comment is deleted
        with self.assertRaises(Comment.DoesNotExist):
            Comment.objects.get(id=comment_id)

        # Test: Admin can create a comment for any article
        self.client.force_authenticate(user=self.admin)
        data = {"body": "Admin comment"}
        response = self.client.post(f"/api/articles/{self.article.id}/comments/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test: Author can view their own comments but cannot view comments from others (403 for others)
        self.client.force_authenticate(user=self.author)
        response = self.client.get(f"/api/comments/{comment_id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # Shouldn't be able to see the deleted comment

        # Test: Commenter can view their own comment
        self.client.force_authenticate(user=self.commenter)
        response = self.client.get(f"/api/comments/{comment_id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) 

    def test_search_and_filtering(self):
        self.client.force_authenticate(user=self.admin)

        # Create additional articles for search testing
        Article.objects.create(title="Django", body="Framework", author=self.author)
        Article.objects.create(title="DRF", body="REST Framework", author=self.author)

        # Search articles by title (pagination will apply, check "results" key)
        response = self.client.get("/api/articles/?search=Django")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)  # Only "Django" should match

        # Ordering articles by title (explicit ordering test)
        response = self.client.get("/api/articles/?ordering=title")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if articles are ordered correctly
        titles = [article["title"] for article in response.data["results"]]
        self.assertEqual(titles, sorted(titles, key=str.lower))  # Ensure titles are sorted alphabetically

    def test_pagination_behavior(self):
        # Authenticate as admin
            self.client.force_authenticate(user=self.admin)

        # Create multiple articles for pagination testing
            for i in range(14):
                Article.objects.create(title=f"Article {i+1}", body="Content", author=self.author)

        # Get first page of articles (should contain 10 results)
            response = self.client.get("/api/articles/?page=1")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), 10)  # PAGE_SIZE = 10

        # Get second page of articles (should contain remaining 5 results)
            response = self.client.get("/api/articles/?page=2")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), 5) 
        

    def test_article_permissions(self):

        
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/articles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

      
        response = self.client.post("/api/articles/", {"title": "New Article", "body": "Content", "is_published": True})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
