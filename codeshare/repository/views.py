from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from datetime import timedelta
from .models import Folder, File, UserLink, Subscription, UserProfile
from .forms import FolderForm, ProfileUpdateForm, UserLinkForm, UserProfileForm
import os
import mimetypes
import re
import json

# Razorpay plan pricing (in paise — INR × 100)
PLAN_PRICES = {
    'pro':     {'amount': 74900,  'label': '₹749/month', 'name': 'Pro Plan'},
    'premium': {'amount': 224900, 'label': '₹2,249/month', 'name': 'Premium Plan'},
}


def home(request):
    folders = Folder.objects.filter(is_public=True).order_by('-created_at')[:6]
    total_folders = Folder.objects.count()
    total_users = User.objects.count()
    return render(request, 'repository/home.html', {
        'folders': folders,
        'total_folders': total_folders,
        'total_users': total_users,
    })


def community(request):
    query = request.GET.get('q', '')
    folders = Folder.objects.filter(is_public=True)
    if query:
        folders = folders.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(tags__icontains=query))
    folders = folders.order_by('-created_at')
    return render(request, 'repository/community.html', {'folders': folders, 'query': query})


def login_view(request):
    from django.contrib.auth import authenticate
    if request.user.is_authenticated:
        return redirect('admin_dashboard' if request.user.is_superuser else 'home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('admin_dashboard' if user.is_superuser else 'home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'repository/login.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            Subscription.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to Deployer 🚀')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'repository/register.html', {'form': form})


@login_required
def create_folder(request):
    if request.method == 'POST':
        form = FolderForm(request.POST)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.owner = request.user
            folder.save()
            messages.success(request, 'Project created successfully!')
            return redirect('upload_files', folder_id=folder.id)
    else:
        form = FolderForm()
    return render(request, 'repository/create_folder.html', {'form': form})


@login_required
def edit_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id, owner=request.user)
    if request.method == 'POST':
        form = FolderForm(request.POST, instance=folder)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully!')
            return redirect('folder_detail', folder_id=folder.id)
    else:
        form = FolderForm(instance=folder)
    return render(request, 'repository/create_folder.html', {'form': form, 'editing': True, 'folder': folder})


def folder_detail(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)

    if not folder.is_public and (not request.user.is_authenticated or request.user != folder.owner):
        messages.error(request, 'This project is private.')
        return redirect('home')

    if not request.user.is_authenticated or request.user != folder.owner:
        folder.visits += 1
        folder.save(update_fields=['visits'])

    files = folder.files.all()
    user_links = folder.owner.links.all()

    return render(request, 'repository/folder_detail.html', {
        'folder': folder,
        'files': files,
        'user_links': user_links,
        'share_link': request.build_absolute_uri(f'/share/{folder.id}/'),
        'has_html_files': files.filter(name__endswith='.html').exists() or files.filter(name__endswith='.htm').exists(),
    })


@login_required
def upload_files(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id, owner=request.user)

    if request.method == 'POST':
        uploaded = request.FILES.getlist('files')
        count = 0
        for uploaded_file in uploaded:
            file_path = request.POST.get(f'path_{uploaded_file.name}', '/')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            File.objects.create(
                folder=folder,
                name=uploaded_file.name,
                file=uploaded_file,
                path=file_path,
                file_type=ext,
                size=uploaded_file.size
            )
            count += 1
        messages.success(request, f'{count} file(s) uploaded successfully!')
        return redirect('folder_detail', folder_id=folder.id)

    return render(request, 'repository/upload_files.html', {'folder': folder})


def file_detail(request, file_id):
    file = get_object_or_404(File, id=file_id)

    if not file.folder.is_public and (not request.user.is_authenticated or request.user != file.folder.owner):
        messages.error(request, 'This project is private.')
        return redirect('home')

    content = None
    if file.is_text():
        try:
            with file.file.open('r') as f:
                content = f.read()
        except Exception:
            content = "Unable to read file content"

    return render(request, 'repository/file_detail.html', {'file': file, 'content': content})


def download_file(request, file_id):
    file = get_object_or_404(File, id=file_id)
    try:
        file.downloads += 1
        file.save(update_fields=['downloads'])
        response = FileResponse(file.file.open('rb'), as_attachment=True, filename=file.name)
        return response
    except Exception:
        raise Http404("File not found")


@login_required
def delete_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id, owner=request.user)
    if request.method == 'POST':
        folder.delete()
        messages.success(request, 'Project deleted successfully!')
        return redirect('user_settings')
    return redirect('folder_detail', folder_id=folder_id)


@login_required
def delete_file(request, file_id):
    file = get_object_or_404(File, id=file_id, folder__owner=request.user)
    folder_id = file.folder.id
    if request.method == 'POST':
        file.delete()
        messages.success(request, 'File deleted successfully!')
        return redirect('folder_detail', folder_id=folder_id)
    return redirect('file_detail', file_id=file_id)


@login_required
def user_settings(request):
    user_folders = Folder.objects.filter(owner=request.user).order_by('-created_at')
    user_links = UserLink.objects.filter(user=request.user)
    subscription, _ = Subscription.objects.get_or_create(user=request.user)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    return render(request, 'repository/settings.html', {
        'user_folders': user_folders,
        'user_links': user_links,
        'subscription': subscription,
        'profile': profile,
    })


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('user_settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'repository/change_password.html', {'form': form})


@login_required
def update_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = ProfileUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user_settings')
    else:
        user_form = ProfileUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    return render(request, 'repository/update_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@login_required
def add_link(request):
    if request.method == 'POST':
        form = UserLinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.user = request.user
            link.save()
            messages.success(request, 'Link added successfully!')
            return redirect('user_settings')
    else:
        form = UserLinkForm()
    return render(request, 'repository/add_link.html', {'form': form})


@login_required
def delete_link(request, link_id):
    link = get_object_or_404(UserLink, id=link_id, user=request.user)
    if request.method == 'POST':
        link.delete()
        messages.success(request, 'Link deleted successfully!')
    return redirect('user_settings')


@login_required
def subscription_plans(request):
    subscription, _ = Subscription.objects.get_or_create(user=request.user)
    return render(request, 'repository/subscription_plans.html', {'subscription': subscription})


@login_required
def upgrade_subscription(request, plan):
    if plan not in ['pro', 'premium', 'free']:
        messages.error(request, 'Invalid subscription plan.')
        return redirect('subscription_plans')

    subscription, _ = Subscription.objects.get_or_create(user=request.user)
    subscription.plan = plan
    subscription.is_active = True
    subscription.save()
    messages.success(request, f'Successfully switched to {plan.title()} plan!')
    return redirect('user_settings')


@login_required
def create_payment_order(request, plan):
    """Create a Razorpay order and return order details."""
    if plan not in PLAN_PRICES:
        return JsonResponse({'error': 'Invalid plan'}, status=400)

    try:
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        price = PLAN_PRICES[plan]
        order = client.order.create({
            'amount': price['amount'],
            'currency': 'INR',
            'payment_capture': 1,
            'notes': {
                'user_id': str(request.user.id),
                'username': request.user.username,
                'plan': plan,
            }
        })

        return JsonResponse({
            'order_id': order['id'],
            'amount': price['amount'],
            'currency': 'INR',
            'key': settings.RAZORPAY_KEY_ID,
            'plan': plan,
            'plan_name': price['name'],
            'user_name': request.user.get_full_name() or request.user.username,
            'user_email': request.user.email or '',
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
def verify_payment(request):
    """Verify Razorpay payment signature and activate subscription."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        import razorpay
        data = json.loads(request.body)

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Verify signature
        client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature'],
        })

        # Activate subscription
        plan = data.get('plan')
        if plan not in ['pro', 'premium']:
            return JsonResponse({'error': 'Invalid plan'}, status=400)

        subscription, _ = Subscription.objects.get_or_create(user=request.user)
        subscription.plan = plan
        subscription.is_active = True
        subscription.save()

        return JsonResponse({'success': True, 'plan': plan})

    except Exception as e:
        return JsonResponse({'error': 'Payment verification failed', 'detail': str(e)}, status=400)


@login_required
def payment_success(request, plan):
    """Show payment success page."""
    subscription, _ = Subscription.objects.get_or_create(user=request.user)
    return render(request, 'repository/payment_success.html', {
        'plan': plan,
        'subscription': subscription,
    })


@login_required
def downgrade_to_free(request):
    if request.method == 'POST':
        subscription, _ = Subscription.objects.get_or_create(user=request.user)
        subscription.plan = 'free'
        subscription.save()
        messages.success(request, 'Downgraded to Free plan.')
    return redirect('subscription_plans')


@login_required
def update_custom_domain(request):
    subscription = get_object_or_404(Subscription, user=request.user)

    if not subscription.can_use_custom_domain():
        messages.error(request, 'Custom domains are only available for Pro and Premium users.')
        return redirect('subscription_plans')

    if request.method == 'POST':
        domain = request.POST.get('custom_domain', '').strip()
        if domain:
            if ' ' in domain or '.' not in domain:
                messages.error(request, 'Please enter a valid domain name.')
            else:
                subscription.custom_domain = domain
                subscription.save()
                messages.success(request, f'Custom domain set to: {domain}')
        else:
            subscription.custom_domain = None
            subscription.save()
            messages.success(request, 'Custom domain removed.')
        return redirect('user_settings')

    return render(request, 'repository/update_custom_domain.html', {'subscription': subscription})


def share_page(request, folder_id):
    """Clean public share page — no account UI, just the project."""
    folder = get_object_or_404(Folder, id=folder_id)

    if not folder.is_public:
        return render(request, 'repository/share_private.html', {'folder': folder})

    # Count visit
    folder.visits += 1
    folder.save(update_fields=['visits'])

    files = folder.files.all()
    user_links = folder.owner.links.all()
    html_files = files.filter(name__endswith='.html')
    main_html = None
    for f in html_files:
        if f.name.lower() == 'index.html':
            main_html = f
            break
    if not main_html and html_files.exists():
        main_html = html_files.first()

    return render(request, 'repository/share_page.html', {
        'folder': folder,
        'files': files,
        'user_links': user_links,
        'main_html': main_html,
        'share_url': request.build_absolute_uri(),
    })


def preview_website(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)

    if not folder.is_public and (not request.user.is_authenticated or request.user != folder.owner):
        messages.error(request, 'This project is private.')
        return redirect('home')

    if not request.user.is_authenticated or request.user != folder.owner:
        folder.visits += 1
        folder.save(update_fields=['visits'])

    html_files = folder.files.filter(name__endswith='.html').order_by('name')
    main_file = None
    for f in html_files:
        if f.name.lower() == 'index.html':
            main_file = f
            break
    if not main_file and html_files.exists():
        main_file = html_files.first()

    if not main_file:
        messages.error(request, 'No HTML files found in this project.')
        return redirect('folder_detail', folder_id=folder_id)

    return render(request, 'repository/preview_website.html', {
        'folder': folder,
        'main_file': main_file,
        'html_files': list(html_files),
    })


def preview_file_as_website(request, file_id):
    file = get_object_or_404(File, id=file_id)
    if file.get_extension() not in ['.html', '.htm']:
        messages.error(request, 'Only HTML files can be previewed as websites.')
        return redirect('file_detail', file_id=file_id)
    return render(request, 'repository/preview_website.html', {
        'folder': file.folder,
        'main_file': file,
        'html_files': [file],
    })


def serve_website_file(request, file_id):
    file = get_object_or_404(File, id=file_id)
    try:
        content = file.file.read().decode('utf-8', errors='replace')
        folder = file.folder

        css_files = folder.files.filter(file_type__in=['.css', 'css'])
        js_files = folder.files.filter(file_type__in=['.js', 'js'])

        inline_css = ''
        for css in css_files:
            try:
                inline_css += css.file.read().decode('utf-8', errors='replace') + '\n'
            except Exception:
                pass

        inline_js = ''
        for js in js_files:
            try:
                inline_js += js.file.read().decode('utf-8', errors='replace') + '\n'
            except Exception:
                pass

        content = re.sub(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<link[^>]+href=["\'][^"\']*\.css["\'][^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<script[^>]+src=["\'][^"\']*\.js["\'][^>]*>\s*</script>', '', content, flags=re.IGNORECASE)

        css_tag = f'<style>{inline_css}</style>' if inline_css else ''
        js_tag = f'<script>{inline_js}</script>' if inline_js else ''

        if '</head>' in content:
            content = content.replace('</head>', f'{css_tag}</head>', 1)
        else:
            content = css_tag + content

        if '</body>' in content:
            content = content.replace('</body>', f'{js_tag}</body>', 1)
        else:
            content = content + js_tag

        response = HttpResponse(content, content_type='text/html; charset=utf-8')
        response['X-Frame-Options'] = 'SAMEORIGIN'
        return response
    except Exception:
        raise Http404("File not found")


# ── Admin ──────────────────────────────────────────────────────────────────────

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            messages.error(request, 'Admin access required.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@admin_required
def admin_dashboard(request):
    total_users = User.objects.count()
    active_users = User.objects.filter(last_login__gte=timezone.now() - timedelta(days=30)).count()
    total_files = File.objects.count()
    total_folders = Folder.objects.count()
    public_folders = Folder.objects.filter(is_public=True).count()
    private_folders = Folder.objects.filter(is_public=False).count()
    total_storage = File.objects.aggregate(total=Sum('size'))['total'] or 0
    recent_users = User.objects.order_by('-date_joined')[:10]
    recent_folders = Folder.objects.order_by('-created_at')[:10]

    return render(request, 'repository/admin_dashboard.html', {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': total_users - active_users,
        'total_files': total_files,
        'total_folders': total_folders,
        'public_folders': public_folders,
        'private_folders': private_folders,
        'total_storage': total_storage,
        'recent_users': recent_users,
        'recent_folders': recent_folders,
    })


@admin_required
def admin_users(request):
    users = User.objects.annotate(
        folder_count=Count('folders'),
        file_count=Count('folders__files')
    ).order_by('-date_joined')
    return render(request, 'repository/admin_users.html', {'users': users})


@admin_required
def admin_user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    folders = Folder.objects.filter(owner=user).annotate(file_count=Count('files'))
    subscription = Subscription.objects.filter(user=user).first()
    total_files = File.objects.filter(folder__owner=user).count()
    total_storage = File.objects.filter(folder__owner=user).aggregate(total=Sum('size'))['total'] or 0

    return render(request, 'repository/admin_user_detail.html', {
        'user_obj': user,
        'folders': folders,
        'subscription': subscription,
        'total_files': total_files,
        'total_storage': total_storage,
        'public_folders': folders.filter(is_public=True).count(),
        'private_folders': folders.filter(is_public=False).count(),
    })


@admin_required
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, 'Cannot delete admin users.')
        return redirect('admin_users')
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" deleted.')
        return redirect('admin_users')
    return redirect('admin_user_detail', user_id=user_id)


@admin_required
def admin_toggle_user_status(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, 'Cannot modify admin users.')
        return redirect('admin_users')
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User "{user.username}" {status}.')
    return redirect('admin_user_detail', user_id=user_id)


@admin_required
def admin_folders(request):
    folders = Folder.objects.annotate(file_count=Count('files')).select_related('owner').order_by('-created_at')
    return render(request, 'repository/admin_folders.html', {'folders': folders})


@admin_required
def admin_delete_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    if request.method == 'POST':
        name = folder.name
        owner = folder.owner.username
        folder.delete()
        messages.success(request, f'Folder "{name}" by {owner} deleted.')
        return redirect('admin_folders')
    return redirect('admin_folders')


@admin_required
def admin_toggle_folder_visibility(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    if request.method == 'POST':
        folder.is_public = not folder.is_public
        folder.save()
        status = 'public' if folder.is_public else 'private'
        messages.success(request, f'Folder "{folder.name}" is now {status}.')
    return redirect('admin_folders')


def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard')
    if request.method == 'POST':
        from django.contrib.auth import authenticate, login as auth_login
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user and user.is_superuser:
            auth_login(request, user)
            messages.success(request, f'Welcome, {user.username}!')
            return redirect('admin_dashboard')
        elif user:
            messages.error(request, 'Admin privileges required.')
        else:
            messages.error(request, 'Invalid credentials.')
    return render(request, 'repository/admin_login.html')


def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('home')
