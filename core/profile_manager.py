import os
import yaml
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ProfileManager:
    def __init__(self, profiles_root: str):
        self.profiles_root = profiles_root
        self.current_profile: Optional[Dict[str, Any]] = None
        self.current_profile_name: str = ""

    def list_profiles(self) -> list[str]:
        """Returns a list of available profile names."""
        if not os.path.exists(self.profiles_root):
            return []
        
        return [
            d for d in os.listdir(self.profiles_root)
            if os.path.isdir(os.path.join(self.profiles_root, d))
            and os.path.exists(os.path.join(self.profiles_root, d, "config.yaml"))
        ]

    def load_profile(self, profile_name: str) -> bool:
        """Loads a specific profile by name."""
        profile_path = os.path.join(self.profiles_root, profile_name)
        config_path = os.path.join(profile_path, "config.yaml")

        if not os.path.exists(config_path):
            logger.error(f"Profile {profile_name} not found or invalid at {profile_path}")
            return False

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.current_profile = yaml.safe_load(f)
                self.current_profile_name = profile_name
                # Add system paths
                self.current_profile['path'] = profile_path
                self.current_profile['prompts_dir'] = os.path.join(profile_path, 'prompts')
                self.current_profile['templates_dir'] = os.path.join(profile_path, 'custom_templates')
            
            logger.info(f"Loaded profile: {self.current_profile.get('name', profile_name)}")
            return True
        except Exception as e:
            logger.error(f"Failed to load profile config: {e}")
            return False

    def get_config(self, key: str, default: Any = None) -> Any:
        """Retrieve a config value from the currently loaded profile."""
        if not self.current_profile:
            return default
        return self.current_profile.get(key, default)

    def get_template_path(self, template_file: str) -> Optional[str]:
        """
        Locates a template file. 
        Priority: 
        1. Profile specific 'custom_templates' folder
        2. Global 'templates' folder (Universal_Generator/templates)
        """
        if not self.current_profile:
            return None

        # 1. Profile Level
        p_level = os.path.join(self.current_profile['path'], 'custom_templates', template_file)
        if os.path.exists(p_level):
            return p_level

        # 2. Global Level
        # self.profiles_root is usually Universal_Generator/profiles
        # We want Universal_Generator/templates
        global_root = os.path.dirname(self.profiles_root)
        g_level = os.path.join(global_root, 'templates', template_file)
        if os.path.exists(g_level):
            return g_level

        return None
