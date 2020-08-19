from django.contrib import admin

from test_verifier.models import Codec, FeatureCategory, Feature, SubFeature

admin.site.register(Codec)
admin.site.register(FeatureCategory)
admin.site.register(Feature)


@admin.register(SubFeature)
class SubFeatureAdmin(admin.ModelAdmin):
    # TODO show also lin_platform and win_platform
    list_display = ('name', 'category', 'feature', 'codec', 'notes')
    ordering = ('name',)
    search_fields = ('name', 'category', 'feature', 'codec', 'notes')
    list_filter = ('category', 'codec', 'feature',)
