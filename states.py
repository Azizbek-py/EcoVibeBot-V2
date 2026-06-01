from aiogram.fsm.state import State, StatesGroup

class RegisterStates(StatesGroup):
    full_name = State()
    phone = State()
    address = State()

class EditProfileStates(StatesGroup):
    choose_field = State()
    full_name = State()
    address = State()

class AddMissionStates(StatesGroup):
    number = State()
    mission_type = State()
    title = State()
    description = State()
    ecopoint = State()
    media = State()

class ScoreMissionStates(StatesGroup):
    select_submission = State()
    quality = State()
    time_score = State()

class AdminScoreMissionStates(StatesGroup):
    select_submission = State()
    quality = State()
    time_score = State()

class SubmitMissionStates(StatesGroup):
    select_mission = State()
    content = State()

class AddCoordinatorStates(StatesGroup):
    telegram_id = State()

class AddInspectorStates(StatesGroup):
    telegram_id = State()

class AssignGroupStates(StatesGroup):
    group_number = State()
    coordinator_id = State()

class BroadcastStates(StatesGroup):
    content = State()

class SearchUserStates(StatesGroup):
    query = State()

class AdjustScoreStates(StatesGroup):
    delta = State()

class AdjustEcopointStates(StatesGroup):
    delta = State()

class GroupSearchStates(StatesGroup):
    group_number = State()

class MissionArchiveStates(StatesGroup):
    mission_number = State()
    group_number = State()

class InspectorMissionStates(StatesGroup):
    group_number = State()
    mission_number = State()

class CoordMissionStates(StatesGroup):
    choose = State()
    mission_number = State()

class MissionVerifyStates(StatesGroup):
    mission_number = State()
    mission_type = State()

class DeleteMissionStates(StatesGroup):
    confirm = State()

class UserMissionStates(StatesGroup):
    choosing = State()   # Asosiy / Bonus / Tarix tanlash
class AddProductStates(StatesGroup):
    name = State()
    description = State()
    price = State()
    emoji = State()

class EventCheckStates(StatesGroup):
    event_number = State()
    group_number = State()

class EventSubmitStates(StatesGroup):
    photo = State()

class AddEventStates(StatesGroup):
    number = State()
    title = State()
    description = State()
    event_time = State()
    ball_reward = State()
    eco_reward = State()
    region = State()
    photo = State()

class InspectorMainMenuStates(StatesGroup):
    choosing = State()

class InspectorMissionsStates(StatesGroup):
    choosing_type = State()
    group_number = State()

class InspectorUsersStates(StatesGroup):
    choosing_submenu = State()
    search_query = State()
    group_number = State()

class InspectorEventsStates(StatesGroup):
    group_number = State()

