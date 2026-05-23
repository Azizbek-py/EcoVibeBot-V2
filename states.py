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
    title = State()
    description = State()
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

class GroupSearchStates(StatesGroup):
    group_number = State()

class MissionArchiveStates(StatesGroup):
    mission_number = State()
    group_number = State()

class InspectorMissionStates(StatesGroup):
    group_number = State()
    mission_number = State()

class CoordMissionStates(StatesGroup):
    mission_number = State()

class DeleteMissionStates(StatesGroup):
    confirm = State()
