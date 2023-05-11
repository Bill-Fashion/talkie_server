"""chatapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import *
from chat.views import *
from notification.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', TokenDeleteView.as_view(), name='logout'),
    path('search/', UserSearchView.as_view(), name='user_search'),
    path('update-user/', UpdateUser.as_view()),
    path('user/info/<uuid:user_id>/', UserInfo.as_view(), name='user_info'),
    
    path('friend/request/', SendFriendRequest.as_view(), name='send_friend_request'),
    path('friend/request/<uuid:user_id>/', FriendRequests.as_view(), name='friend_requests'),
    path('friend/request/<int:id>/', DeleteUserFriendRequest.as_view(), name='delete_user_friend_request'),
    path('friend/accept/<int:request_id>/', AcceptFriendRequest.as_view(), name='accept_friend_request'),
    path('friend/list/<uuid:user_id>/', UserFriendList.as_view(), name='friends_list'),
    path('friend/relationship/status/', GetRelationshipStatus.as_view(), name='relationship_status'),
    
    path('rooms/create/', RoomCreateView.as_view(), name='room-create'),
    path('rooms/<uuid:user_id>/', GetRoomsInfo.as_view()),
    path('rooms/<uuid:user_id1>/<uuid:user_id2>/', GetRoom.as_view(), name='get_room'),
    path('messages/<uuid:room_id>/', GetLatestMessages.as_view()),

    path('save-token/', SaveToken.as_view()),
    path('push-notification/', PushNotification.as_view()),

    path('', include('chat.urls'))
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
