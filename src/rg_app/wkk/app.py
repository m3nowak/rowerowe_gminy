import asyncio
import logging
import tempfile
from datetime import UTC, datetime, timedelta

import geopandas as gpd
import httpx
import msgspec.json
import nats.js.errors
import polyline
import shapely.geometry as sg
import sqlalchemy as sa

# import strava_api
from nats import connect as nats_connect
from nats.aio.msg import Msg
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from rg_app.common.strava import StravaTokenManager
from rg_app.db.models import User

from .config import Config
from .models import ActivityPartial, LoginData
from .strava_auth import StravaAuth

logging.basicConfig(level=logging.INFO)

async def main(config: Config):
    nc = await nats_connect(
        config.nats.url, user_credentials=config.nats.creds_path, inbox_prefix=config.nats.inbox_prefix
    )
    js = nc.jetstream(domain=config.nats.js_domain)

    sa_engine = create_async_engine(
        config.db.get_url(),
    )
    sa_sm = async_sessionmaker(sa_engine, expire_on_commit=False)

    stm = StravaTokenManager(config.strava_client_id, config.get_strava_client_secret())

    kv = await js.key_value(config.nats.login_kv)

    async def handle_update(msg: Msg):
        msg_loaded: dict[str, str | int | dict] = msgspec.json.decode(msg.data)
        activity_id = msg_loaded.get("object_id")
        owner_id = msg_loaded.get("owner_id")
        assert isinstance(owner_id, int) and isinstance(activity_id, int)
        logging.info(f"Received update for activity {activity_id} for owner {owner_id}")
        try:
            owner_in_kv = await kv.get(str(owner_id))
        except nats.js.errors.KeyNotFoundError:
            owner_in_kv = None

        if owner_in_kv is None or owner_in_kv.value is None:
            logging.info(f"Owner {owner_id} not found in KV")
            await msg.respond(b"")
            return

        owner_login_data = msgspec.json.decode(owner_in_kv.value, type=LoginData)

        user_access_token = None

        async with sa_sm() as session:
            result = await session.execute(sa.select(User).filter(User.id == owner_id))
            user = result.scalars().one_or_none()
            if user is None:
                logging.info(f"Owner {owner_id} not found in DB")
                await msg.respond(b"")
                return
            
            # Check if the token is expired or missing
            now = datetime.now(UTC)
            if user.access_token is None or user.expires_at < now + timedelta(minutes=5):
                logging.info(f"Owner {owner_id} missing refresh token or token expired")
                async with stm.begin():
                    new_token = await stm.refresh(user.refresh_token)
                    user.access_token = new_token.access_token
                    user.expires_at = new_token.expires_at
                    await session.commit()
            user_access_token = user.access_token
        
        assert user_access_token is not None

        auth = StravaAuth(user_access_token)
        # client = httpx.AsyncClient(auth=auth)
        # strava = strava_api.AuthenticatedClient('https://www.strava.com/api/v3', token=user_access_token)
        
        # Get activity detail
        da = None
        async with httpx.AsyncClient(auth=auth) as strava:
            resp = await strava.get(f"https://www.strava.com/api/v3/activities/{activity_id}")
            if resp.status_code == 200:
                da = msgspec.json.decode(resp.text, type=ActivityPartial)
            else:
                logging.info(f"Failed to get activity {activity_id}, status code {resp.status_code}")
                await msg.respond(b"")
                return

        # Check if activity is a Ride
        if da is None:
            logging.info(f"Activity {activity_id} not found")
            await msg.respond(b"")
            return
        if da.type != "Ride":
            logging.info(f"Activity {activity_id} is not a Ride")
            await msg.respond(b"")
            return
        if not da.map or not da.map.polyline:
            logging.info(f"Activity {activity_id} has no map or polyline")
            await msg.respond(b"")
            return
        
        # Decode polyline and save as GPX
        decoded_polyline = polyline.decode(da.map.polyline, geojson=True)
        gdf = gpd.GeoDataFrame({'geometry':[sg.LineString(decoded_polyline)]})
        gdf.to_file("data/decoded_polyline.gpx", driver="GPX")
        gpx_string = None
        #TODO Change to aiofiles
        with tempfile.NamedTemporaryFile(delete=True, suffix='.gpx') as temp_file:
            gdf.to_file(temp_file.name, driver="GPX")
            gpx_string = temp_file.read()
        assert gpx_string is not None

        # generate strava url
        strava_url = f"https://www.strava.com/activities/{activity_id}"

        #TODO implement the rest
        await msg.respond(b"")
    await nc.subscribe(config.nats.consumer_deliver_subject, cb=handle_update)

    logging.info(f"Subscribed to {config.nats.consumer_deliver_subject}")
    while True:
        await asyncio.sleep(1)
