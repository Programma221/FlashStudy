from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .utils import summarize_text, generate_flashcards
from .models import FlashcardSet, Flashcard
import json


@login_required(login_url='accounts/login')
def core_view(request):
    submitted_text = request.POST.get('text_content', '')
    summary = ""
    flashcards = None
    summary_requested = False
    save_success = False

    if request.method == "POST":
        if "summarize" in request.POST:
            summary = summarize_text(submitted_text)
            summary_requested = True
        elif "generate_flashcard" in request.POST:
            num_cards = int(request.POST.get('num_cards', 3))
            flashcards = generate_flashcards(submitted_text, num_cards)
        elif "save_flashcards" in request.POST:
            # Save flashcards functionality
            flashcards_data = request.POST.get('flashcards_data')
            set_title = request.POST.get('set_title', 'Untitled Set')

            if flashcards_data:
                try:
                    flashcards_list = json.loads(flashcards_data)

                    # Create flashcard set
                    flashcard_set = FlashcardSet.objects.create(
                        title=set_title,
                        user=request.user
                    )

                    # Create individual flashcards
                    for question, answer in flashcards_list:
                        Flashcard.objects.create(
                            flashcard_set=flashcard_set,
                            question=question,
                            answer=answer
                        )

                    save_success = True
                    flashcards = flashcards_list  # Keep flashcards visible
                except json.JSONDecodeError:
                    save_success = False

    # Get user's flashcard sets
    flashcard_sets = FlashcardSet.objects.filter(user=request.user)

    context = {
        "submitted_text": submitted_text,
        "summary": summary,
        "flashcards": flashcards,
        "flashcards_json": json.dumps(flashcards) if flashcards else None,
        "summary_requested": summary_requested,
        "flashcard_sets": flashcard_sets,
        "save_success": save_success,
    }
    return render(request, "core/core.html", context)


@login_required(login_url='accounts/login')
def load_flashcard_set(request, set_id):
    """Load a specific flashcard set for studying"""
    flashcard_set = get_object_or_404(FlashcardSet, id=set_id,
                                      user=request.user)
    flashcards = [(card.question, card.answer) for card in
                  flashcard_set.cards.all()]

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request
        return JsonResponse({
            'success': True,
            'flashcards': flashcards,
            'set_title': flashcard_set.title
        })

    # Regular request - redirect back to main page with flashcards loaded
    context = {
        "flashcards": flashcards,
        "flashcards_json": json.dumps(flashcards),
        "flashcard_sets": FlashcardSet.objects.filter(user=request.user),
        "loaded_set_title": flashcard_set.title,
    }
    return render(request, "core/core.html", context)


@login_required(login_url='accounts/login')
def delete_flashcard_set(request, set_id):
    """Delete a flashcard set"""
    if request.method == "POST":
        flashcard_set = get_object_or_404(FlashcardSet, id=set_id,
                                          user=request.user)
        flashcard_set.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

    return redirect('core')