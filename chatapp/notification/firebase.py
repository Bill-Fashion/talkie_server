import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
from channels.db import database_sync_to_async
from accounts.models import *
from chat.models import Room


# Initialize Firebase Admin SDK with your service account credentials
cred = credentials.Certificate('./talkie-9c2c6-firebase-adminsdk-lbkg6-82371d3db6.json')
firebase_admin.initialize_app(cred)

# @database_sync_to_async
# def get_room(room_id):
#     return Room.objects.get(id=room_id)

# @database_sync_to_async
# def get_user(sender_id):
#     return CustomUser.objects.get(user_id=sender_id)

@database_sync_to_async
def delete_tokens(token):
    UserDevice.objects.filter(device_token=token).delete()

def push_notification(registration_tokens, senderId, roomId):
    # sender = await get_user(senderId)
    # room = await get_room(roomId)
    # other_members = room.members.exclude(user_id=senderId).first()
    # registration_devices = UserDevice.objects.filter(user=other_members[0])
    # registration_tokens = [registration_device.device_token for registration_device in registration_devices]

    # Compose the message to be sent
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=f'{senderId} {roomId}',
            body=f'{senderId} sent a new message in {roomId}',
        ),
        tokens=registration_tokens,
    )
    
    # Send the message via FCM
    response = messaging.send_multicast(message)
    # print("Response: ", response)
    # Check for any failures and log them
    if response.failure_count > 0:
        responses = response.responses
        failed_tokens = []
        for idx, resp in enumerate(responses):
            # print(f'Sending message to {registration_tokens[idx]}: {resp}')
            if not resp.success:
                # The order of responses corresponds to the order of the registration tokens.
                failed_tokens.append(registration_tokens[idx])
        for token in failed_tokens:
            delete_tokens(token)
