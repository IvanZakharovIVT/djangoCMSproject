# api/serializers.py
import json
from django.core.serializers.json import DjangoJSONEncoder
from cms.models.pluginmodel import CMSPlugin


class PluginSerializer:
    """Простой сериализатор для плагинов CMS"""

    @staticmethod
    def serialize_plugin(plugin):
        """Сериализует один плагин в словарь"""
        # Базовая информация о плагине
        data = {
            'id': plugin.id,
            'plugin_type': plugin.plugin_type,
            'position': plugin.position,
            'language': plugin.language,
            'placeholder': {
                'id': plugin.placeholder_id,
                'slot': plugin.placeholder.slot if plugin.placeholder else None,
            },
            'creation_date': plugin.creation_date.isoformat() if plugin.creation_date else None,
        }

        # Получаем специфические данные плагина (если есть)
        try:
            # Пытаемся получить экземпляр конкретного типа плагина
            plugin_instance = plugin.get_plugin_instance()[0]
            if plugin_instance:
                # Получаем данные из конкретного плагина
                if hasattr(plugin_instance, 'get_plugin_data'):
                    data['data'] = plugin_instance.get_plugin_data()
                elif hasattr(plugin_instance, 'body'):
                    # Например, для текстового плагина
                    data['data'] = {'body': plugin_instance.body}
                elif hasattr(plugin_instance, 'file'):
                    # Для плагина файла
                    data['data'] = {'file_url': plugin_instance.file.url if plugin_instance.file else None}
                # Добавьте другие типы плагинов по необходимости
        except Exception:
            # Если не удалось получить конкретные данные, просто пропускаем
            pass

        return data

    @staticmethod
    def serialize_plugins(plugins):
        """Сериализует список плагинов"""
        return [PluginSerializer.serialize_plugin(plugin) for plugin in plugins]
