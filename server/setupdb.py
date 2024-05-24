# setup db based on the models

import asyncio
import logging
import configparser

import asyncpg
import coloredlogs

coloredlogs.install(level="INFO")

tables = dict(
    users="""
  CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    
    spotify_id TEXT UNIQUE,
    email TEXT,
    username TEXT,
    avatar TEXT,
    
    role TEXT DEFAULT 'user',
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    token TEXT,
    
    first_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
       
    enabled_features TEXT[] DEFAULT '{}',
    
    timezone TEXT,
    
    -- daily smash (ds)
    ds_playlist TEXT,    
    ds_update_at TIME,  -- will always be in UTC
    ds_songs_count INT,
    
    -- public liked (pl)
    pl_playlist TEXT,
    
    -- live weather (lw)
    lw_playlist TEXT,
    lw_lat FLOAT,
    lw_lon FLOAT,
    lw_scale TEXT,
    
    -- liked archive (la)
    la_playlist TEXT
    
  );
  """,
    user_stats="""
  CREATE TABLE IF NOT EXISTS user_stats (
    user_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        
    generated_playlists INT DEFAULT 0,
    daily_smashes INT DEFAULT 0,
    filtered_playlists INT DEFAULT 0,
    archived_songs INT DEFAULT 0,
    weather_changes INT DEFAULT 0
  );
  
  """,
    events="""
  CREATE TABLE IF NOT EXISTS events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    
    success BOOLEAN,
    data JSONB DEFAULT '{}'::jsonb
  );
  """,
    user_cache="""
    CREATE TABLE IF NOT EXISTS user_cache (
        user_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        key TEXT,
        value JSONB,
        
        UNIQUE (user_id, key)
    );
    """,
)


async def setup_db(pool: asyncpg.Pool, redo: list | bool = None):
    async with pool.acquire() as conn:
        for table in tables:
            if redo:
                if redo is not True and table not in redo:
                    continue

                logging.info(f"Dropping table {table}")
                await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")

                if table == "runs":
                    logging.info("^ Resetting total_runs from muzee")
                    await conn.execute("UPDATE muzee SET total_runs = 0")

            logging.info(f"Creating table {table}")
            await conn.execute(tables[table])


async def main(*args, **kwargs):
    config = configparser.ConfigParser()
    config.read("config.ini")

    logging.info("Connecting to the database")
    async with asyncpg.create_pool(
        user=config.get("database", "username"),
        password=config.get("database", "password"),
        database=config.get("database", "database"),
    ) as pool:
        logging.info("Setting up the database")
        await setup_db(pool, *args, **kwargs)


if __name__ == "__main__":
    asyncio.run(main(redo=["user_cache"]))
