import os
import pathlib
import traceback

import yaml
from flask import Blueprint, render_template, jsonify, Flask
from opentakserver.plugins.Plugin import Plugin
from opentakserver.extensions import *

from .default_config import DefaultConfig
import importlib.metadata


class PluginTemplate(Plugin):
    # Change the Blueprint name to YourPluginBlueprint
    url_prefix = f"/api/plugins/{pathlib.Path(__file__).resolve().parent.name}"
    blueprint = Blueprint("PluginTemplate", __name__, url_prefix=url_prefix, template_folder="templates")

    def activate(self, app: Flask):
        self._app = app
        self._load_config()
        self._load_metadata()

        try:
            # Do stuff here
            logger.info(f"Successfully Loaded {self._name}")
        except BaseException as e:
            logger.error(f"Failed to load {self._name}: {e}")
            logger.error(traceback.format_exc())

    # Loads default config and user config from ~/ots/config.yml
    # In most cases you don't need to change this
    def _load_config(self):
        # Gets default config key/value pairs from default_config.py
        for key in dir(DefaultConfig):
            if key.isupper():
                self._config[key] = getattr(DefaultConfig, key)

        # Get user overrides from config.yml
        with open(os.path.join(self._app.config.get("OTS_DATA_FOLDER"), "config.yml")) as yaml_file:
            yaml_config = yaml.safe_load(yaml_file)
            for key in self._config.keys():
                value = yaml_config.get(key)
                if value:
                    self._config[key] = value

    def _load_metadata(self):
        try:
            distributions = importlib.metadata.packages_distributions()
            for distro in distributions:
                if str(__name__).startswith(distro):
                    self._name = distributions[distro][0]
                    self._distro = distro
                    info = importlib.metadata.metadata(self._distro)
                    self._metadata = info.json
                    break

        except BaseException as e:
            logger.error(e)

    def get_info(self):
        self._load_metadata()
        self.get_plugin_routes(self.url_prefix)
        return {'name': self._name, 'distro': self._distro, 'routes': self._routes}

    def stop(self):
        # Shut down your plugin gracefully here
        pass

    # Make route methods static to avoid "no-self-use" errors
    @staticmethod
    @blueprint.route("/")
    def plugin_info():  # Do not put "self" as a method parameter here
        # This method will return JSON with info about the plugin derived from pyproject.toml, please do not change it
        try:
            distribution = None
            distributions = importlib.metadata.packages_distributions()
            for distro in distributions:
                if str(__name__).startswith(distro):
                    distribution = distributions[distro][0]
                    break

            if distribution:
                info = importlib.metadata.metadata(distribution)
                return jsonify(info.json)
            else:
                return jsonify({'success': False, 'error': 'Plugin not found'}), 404
        except BaseException as e:
            logger.error(e)
            return jsonify({'success': False, 'error': e}), 500

    # OpenTAKServer's web UI will call your plugin's /ui endpoint and display the results
    # Delete this if your plugin doesn't require a UI
    @staticmethod
    @blueprint.route("/ui")
    def ui():
        return render_template("index.html")

    # Add more routes here. Make sure to use try/except blocks around all of your code. Otherwise, an exception in a plugin
    # could cause the whole server to crash
