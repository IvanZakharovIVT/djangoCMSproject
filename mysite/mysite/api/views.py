# api/views.py
import json
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch

from cms.models import Page
from cms.models.contentmodels import PageContent
from cms.models.pluginmodel import CMSPlugin

from .serializers import PluginSerializer


class PagePluginsAPIView(View):
    """
    API для получения всех плагинов на странице
    """

    def get(self, request, page_id):
        """
        GET /api/page/<page_id>/plugins/

        Параметры запроса:
        - language: язык страницы (опционально, если не указан - возвращаются все языки)
        - slot: фильтр по слоту (опционально)
        - format: 'json' или 'pretty' (для форматированного вывода)
        """

        # Получаем параметры запроса
        language = request.GET.get('language')
        slot = request.GET.get('slot')
        pretty = request.GET.get('format') == 'pretty'

        try:
            # Получаем страницу
            page = Page.objects.get(pk=page_id)

            # Получаем PageContent для страницы
            page_contents = PageContent.objects.filter(page=page)

            # Фильтруем по языку, если указан
            if language:
                page_contents = page_contents.filter(language=language)

            if not page_contents.exists():
                return JsonResponse({
                    'error': f'No content found for page {page_id}',
                    'languages_available': list(
                        PageContent.objects.filter(page=page).values_list('language', flat=True))
                }, status=404)

            # Собираем все плагины
            result = {
                'page_id': page_id,
                'page_title': page.get_title(),
                'plugins': [],
                'summary': {
                    'total_plugins': 0,
                    'by_slot': {},
                    'by_language': {}
                }
            }

            # Получаем плагины для каждого PageContent
            for page_content in page_contents:
                # Получаем все placeholders для этого PageContent
                placeholders = page_content.placeholders.all()

                # Фильтруем по слоту, если указан
                if slot:
                    placeholders = placeholders.filter(slot=slot)

                # Получаем плагины из этих placeholders
                plugins = CMSPlugin.objects.filter(
                    placeholder__in=placeholders
                ).order_by('placeholder__slot', 'position')

                # Сериализуем плагины
                serialized_plugins = PluginSerializer.serialize_plugins(plugins)

                # Добавляем в результат
                result['plugins'].extend(serialized_plugins)

                # Обновляем статистику
                lang = page_content.language
                result['summary']['total_plugins'] += len(plugins)

                # Статистика по слотам
                for plugin in plugins:
                    slot_name = plugin.placeholder.slot
                    if slot_name not in result['summary']['by_slot']:
                        result['summary']['by_slot'][slot_name] = 0
                    result['summary']['by_slot'][slot_name] += 1

                # Статистика по языкам
                if lang not in result['summary']['by_language']:
                    result['summary']['by_language'][lang] = 0
                result['summary']['by_language'][lang] += len(plugins)

            # Возвращаем результат
            if pretty:
                return JsonResponse(result, json_dumps_params={'indent': 2, 'ensure_ascii': False})
            return JsonResponse(result)

        except Page.DoesNotExist:
            return JsonResponse({
                'error': f'Page with id {page_id} does not exist'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)


class PlaceholderPluginsAPIView(View):
    """
    API для получения плагинов из конкретного placeholder
    """

    def get(self, request, page_id, slot_name):
        """
        GET /api/page/<page_id>/placeholder/<slot_name>/plugins/
        """

        language = request.GET.get('language')

        try:
            page = Page.objects.get(pk=page_id)
            page_contents = PageContent.objects.filter(page=page)

            if language:
                page_contents = page_contents.filter(language=language)

            result = {
                'page_id': page_id,
                'slot': slot_name,
                'plugins': [],
                'languages': []
            }

            for page_content in page_contents:
                try:
                    placeholder = page_content.placeholders.get(slot=slot_name)
                    plugins = placeholder.get_plugins().order_by('position')

                    result['plugins'].append({
                        'language': page_content.language,
                        'plugins': PluginSerializer.serialize_plugins(plugins)
                    })

                    result['languages'].append(page_content.language)

                except ObjectDoesNotExist:
                    # Плейсхолдер не существует для этого языка
                    result['plugins'].append({
                        'language': page_content.language,
                        'plugins': [],
                        'error': f'Placeholder "{slot_name}" not found'
                    })

            if not result['plugins']:
                return JsonResponse({
                    'error': f'No content found for page {page_id}'
                }, status=404)

            return JsonResponse(result)

        except Page.DoesNotExist:
            return JsonResponse({
                'error': f'Page with id {page_id} does not exist'
            }, status=404)


class AllPagesPluginsAPIView(View):
    """
    API для получения плагинов всех страниц
    """

    def get(self, request):
        """
        GET /api/pages/plugins/

        Параметры:
        - limit: ограничение количества страниц
        - language: фильтр по языку
        """

        limit = int(request.GET.get('limit', 10))
        language = request.GET.get('language')

        # Получаем страницы
        pages = Page.objects.filter(publisher_is_draft=False)[:limit]

        result = {
            'pages': [],
            'total_pages': pages.count()
        }

        for page in pages:
            page_data = {
                'id': page.pk,
                'title': page.get_title(),
                'path': page.get_path(),
                'plugins': [],
                'languages': []
            }

            # Получаем PageContent
            page_contents = PageContent.objects.filter(page=page)
            if language:
                page_contents = page_contents.filter(language=language)

            for page_content in page_contents:
                # Получаем все плагины для этой версии страницы
                plugins = CMSPlugin.objects.filter(
                    placeholder__in=page_content.placeholders.all()
                )

                page_data['plugins'].extend(PluginSerializer.serialize_plugins(plugins))
                page_data['languages'].append(page_content.language)

            result['pages'].append(page_data)

        return JsonResponse(result)