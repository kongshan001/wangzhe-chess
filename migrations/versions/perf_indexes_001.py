"""添加性能优化索引

Revision ID: perf_indexes_001
Revises: 
Create Date: 2026-02-22

优化数据库查询性能：
1. 玩家表索引
2. 排位表索引
3. 统计表索引
4. 聊天/观战表索引
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'perf_indexes_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加性能优化索引"""
    
    # 玩家表优化索引
    # 用于快速查找活跃玩家
    op.create_index(
        'ix_players_active_login',
        'players',
        ['is_active', 'last_login_at'],
        mysql_length={'last_login_at': 8},
    )
    
    # 用于排行榜查询
    op.create_index(
        'ix_player_ranks_leaderboard',
        'player_ranks',
        ['season_id', 'tier', 'points'],
    )
    
    # 用于段位统计
    op.create_index(
        'ix_player_ranks_tier_season',
        'player_ranks',
        ['tier', 'season_id'],
    )
    
    # 玩家统计表优化索引
    # 用于胜率排行
    op.create_index(
        'ix_player_stats_winrate',
        'player_stats',
        ['season_id', 'total_wins', 'total_matches'],
    )
    
    # 用于前四率排行
    op.create_index(
        'ix_player_stats_top4',
        'player_stats',
        ['season_id', 'total_top4', 'total_matches'],
    )
    
    # 登录记录优化索引
    # 用于最近登录查询
    op.create_index(
        'ix_player_login_logs_recent',
        'player_login_logs',
        ['player_id', 'login_time'],
    )
    
    # 用于按IP查询
    op.create_index(
        'ix_player_login_logs_ip_time',
        'player_login_logs',
        ['login_ip', 'login_time'],
    )
    
    # 好友表优化索引
    op.create_index(
        'ix_friends_status',
        'friends',
        ['player_id', 'status'],
    )
    
    # 排行榜表优化索引
    op.create_index(
        'ix_leaderboard_rank',
        'leaderboard',
        ['leaderboard_type', 'rank'],
    )
    
    op.create_index(
        'ix_leaderboard_score',
        'leaderboard',
        ['leaderboard_type', 'score'],
    )
    
    # 签到表优化索引
    op.create_index(
        'ix_checkin_date',
        'checkin',
        ['player_id', 'checkin_date'],
    )
    
    # 自定义房间表优化索引
    op.create_index(
        'ix_custom_room_status',
        'custom_room',
        ['status', 'created_at'],
    )
    
    op.create_index(
        'ix_custom_room_creator',
        'custom_room',
        ['creator_id', 'status'],
    )
    
    # 观战聊天表优化索引
    op.create_index(
        'ix_spectator_chat_time',
        'spectator_chat',
        ['game_id', 'sent_at'],
    )
    
    # 回放表优化索引
    op.create_index(
        'ix_replay_game_time',
        'replay',
        ['game_id', 'created_at'],
    )
    
    op.create_index(
        'ix_replay_player',
        'replay',
        ['player_id', 'created_at'],
    )


def downgrade() -> None:
    """移除性能优化索引"""
    
    op.drop_index('ix_replay_player', 'replay')
    op.drop_index('ix_replay_game_time', 'replay')
    op.drop_index('ix_spectator_chat_time', 'spectator_chat')
    op.drop_index('ix_custom_room_creator', 'custom_room')
    op.drop_index('ix_custom_room_status', 'custom_room')
    op.drop_index('ix_checkin_date', 'checkin')
    op.drop_index('ix_leaderboard_score', 'leaderboard')
    op.drop_index('ix_leaderboard_rank', 'leaderboard')
    op.drop_index('ix_friends_status', 'friends')
    op.drop_index('ix_player_login_logs_ip_time', 'player_login_logs')
    op.drop_index('ix_player_login_logs_recent', 'player_login_logs')
    op.drop_index('ix_player_stats_top4', 'player_stats')
    op.drop_index('ix_player_stats_winrate', 'player_stats')
    op.drop_index('ix_player_ranks_tier_season', 'player_ranks')
    op.drop_index('ix_player_ranks_leaderboard', 'player_ranks')
    op.drop_index('ix_players_active_login', 'players')
