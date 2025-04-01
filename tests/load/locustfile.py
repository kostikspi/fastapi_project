from locust import HttpUser, task, between
import random
import string

class URLShortenerUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize user session."""
        self.email = f"test_{random.randint(1000, 9999)}@example.com"
        self.password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        register_data = {
            "email": self.email,
            "password": self.password
        }
        self.client.post("/api/v1/users/register", json=register_data)
        
        login_data = {
            "username": self.email,
            "password": self.password
        }
        response = self.client.post("/api/v1/users/login", data=login_data)
        self.token = response.json()["access_token"]
        self.client.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def create_short_url(self):
        """Create a new short URL."""
        url_data = {
            "original_url": f"https://example.com/{random.randint(1000, 9999)}",
            "custom_alias": f"test_{random.randint(1000, 9999)}"
        }
        self.client.post("/api/v1/links/shorten", json=url_data)
    
    @task(5)
    def redirect_to_url(self):
        """Redirect to a URL."""
        url_data = {
            "original_url": f"https://example.com/{random.randint(1000, 9999)}",
            "custom_alias": f"test_{random.randint(1000, 9999)}"
        }
        response = self.client.post("/api/v1/links/shorten", json=url_data)
        short_code = url_data["custom_alias"]
        
        self.client.get(f"/api/v1/links/{short_code}", allow_redirects=False)
    
    @task(2)
    def get_url_stats(self):
        """Get URL statistics."""
        url_data = {
            "original_url": f"https://example.com/{random.randint(1000, 9999)}",
            "custom_alias": f"test_{random.randint(1000, 9999)}"
        }
        response = self.client.post("/api/v1/links/shorten", json=url_data)
        short_code = url_data["custom_alias"]
        
        self.client.get(f"/api/v1/links/{short_code}/stats")
    
    @task(1)
    def search_url(self):
        """Search for a URL."""
        url_data = {
            "original_url": f"https://example.com/{random.randint(1000, 9999)}",
            "custom_alias": f"test_{random.randint(1000, 9999)}"
        }
        response = self.client.post("/api/v1/links/shorten", json=url_data)
        
        self.client.get(f"/api/v1/links/search?original_url={url_data['original_url']}") 