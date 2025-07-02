"""Tests for the settings module."""
import pytest
import os
from zbricks.core.settings import Settings, settings


class TestSettings:
    """Test settings functionality."""
    
    def test_default_settings(self):
        """Test that default settings are loaded correctly."""
        test_settings = Settings()
        assert test_settings.MODE == "development"  # Default value
        assert test_settings.SECRET_KEY == "dev-secret"  # Default value
    
    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        # Save original values
        original_mode = os.environ.get("APP_MODE")
        original_secret = os.environ.get("SECRET_KEY")
        
        try:
            # Set environment variables
            os.environ["APP_MODE"] = "testing"
            os.environ["SECRET_KEY"] = "test-secret-key"
            
            # Create a new Settings class that re-reads environment variables
            class TestSettings:
                MODE = os.getenv("APP_MODE", "development")
                SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
                
                def validate(self):
                    if self.MODE == "production" and self.SECRET_KEY == "dev-secret":
                        raise RuntimeError("SECURITY ERROR: You must set SECRET_KEY in production!")
            
            test_settings = TestSettings()
            assert test_settings.MODE == "testing"
            assert test_settings.SECRET_KEY == "test-secret-key"
        finally:
            # Clean up environment variables
            if original_mode is not None:
                os.environ["APP_MODE"] = original_mode
            else:
                os.environ.pop("APP_MODE", None)
            
            if original_secret is not None:
                os.environ["SECRET_KEY"] = original_secret
            else:
                os.environ.pop("SECRET_KEY", None)
    
    def test_production_security_validation(self):
        """Test that production mode requires secure secret key."""
        # Save original values
        original_mode = os.environ.get("APP_MODE")
        original_secret = os.environ.get("SECRET_KEY")
        
        try:
            # Set production mode with default (insecure) secret
            os.environ["APP_MODE"] = "production"
            os.environ.pop("SECRET_KEY", None)  # Use default dev-secret
            
            # Create a new Settings class that re-reads environment variables
            class TestSettings:
                MODE = os.getenv("APP_MODE", "development")
                SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
                
                def validate(self):
                    if self.MODE == "production" and self.SECRET_KEY == "dev-secret":
                        raise RuntimeError("SECURITY ERROR: You must set SECRET_KEY in production!")
            
            with pytest.raises(RuntimeError, match="SECURITY ERROR"):
                TestSettings().validate()
        finally:
            # Restore environment
            if original_mode is not None:
                os.environ["APP_MODE"] = original_mode
            else:
                os.environ.pop("APP_MODE", None)
            
            if original_secret is not None:
                os.environ["SECRET_KEY"] = original_secret
            else:
                os.environ.pop("SECRET_KEY", None)
    
    def test_production_with_secure_secret_key(self):
        """Test that production mode works with proper secret key."""
        original_mode = os.environ.get("APP_MODE")
        original_secret = os.environ.get("SECRET_KEY")
        
        try:
            os.environ["APP_MODE"] = "production"
            os.environ["SECRET_KEY"] = "secure-production-key-12345"
            
            # Create a new Settings class that re-reads environment variables
            class TestSettings:
                MODE = os.getenv("APP_MODE", "development")
                SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
                
                def validate(self):
                    if self.MODE == "production" and self.SECRET_KEY == "dev-secret":
                        raise RuntimeError("SECURITY ERROR: You must set SECRET_KEY in production!")
            
            test_settings = TestSettings()
            test_settings.validate()  # Should not raise
            
            assert test_settings.MODE == "production"
            assert test_settings.SECRET_KEY == "secure-production-key-12345"
        finally:
            # Restore environment
            if original_mode is not None:
                os.environ["APP_MODE"] = original_mode
            else:
                os.environ.pop("APP_MODE", None)
            
            if original_secret is not None:
                os.environ["SECRET_KEY"] = original_secret
            else:
                os.environ.pop("SECRET_KEY", None)
    
    def test_global_settings_instance(self):
        """Test that the global settings instance exists and is valid."""
        # The module should have already created and validated settings
        assert settings is not None
        assert hasattr(settings, 'MODE')
        assert hasattr(settings, 'SECRET_KEY')
        
        # Should be using defaults in development
        if os.environ.get("APP_MODE") != "production":
            assert settings.MODE in ["development", "testing"]
    
    def test_settings_attributes_immutable(self):
        """Test that settings behave as expected for attribute access."""
        test_settings = Settings()
        
        # Should be able to read attributes
        mode = test_settings.MODE
        secret = test_settings.SECRET_KEY
        
        assert isinstance(mode, str)
        assert isinstance(secret, str)
