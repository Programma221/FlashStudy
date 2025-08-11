from .models import FlashcardSet, Flashcard

# @admin.register(FlashcardSet)
# class FlashcardSetAdmin(admin.ModelAdmin):
#     list_display = ['title', 'user', 'created_at', 'card_count']
#     list_filter = ['created_at', 'user']
#     search_fields = ['title', 'user__username']
#
#     def card_count(self, obj):
#         return obj.cards.count()
#
#     card_count.short_description = 'Number of Cards'
#
#
# @admin.register(Flashcard)
# class FlashcardAdmin(admin.ModelAdmin):
#     list_display = ['question_preview', 'flashcard_set', 'created_at']
#     list_filter = ['created_at', 'flashcard_set__user']
#     search_fields = ['question', 'answer']
#
#     def question_preview(self, obj):
#         return obj.question[:50] + "..." if len(
#             obj.question) > 50 else obj.question
#
#     question_preview.short_description = 'Question'