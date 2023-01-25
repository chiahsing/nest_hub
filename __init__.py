# Default values for each setting.
_DEFAULT_CONFIG = {
    'boot_delay': 20,
    'dark_theme': None,
    'dashboard_url': None,
    'enable_switch': None,
    'idle_duration': 3 * 60,
    'light_theme': None,
    'mute_before_recast': True,
    'off_duration': 10,
    'paused_duration': 3 * 60,
    'recast_on_start': True,
    'restore_volume_level': True,
}


def _create_device_triggers(entity_id, config):
    """The factory function to create two triggers per Nest Hub device.

    The first one, nest_hub_recast, recasts Nest Hub when necessary.
    The second one, nest_hub_is_unavailable, is used to track if a Nest Hub
    device is rebooted, in which case we need to have an extra 20s delay in
    recasting.
    """
    log.info('Create device triggers for {} with config {}'.format(
        entity_id, config))

    nest_hub = entity_id[entity_id.find('.') + 1:]
    avail_state = f'pyscript.{nest_hub}_availability'
    state.persist(avail_state, default_value='1')
    volume_level_state = f'pyscript.{nest_hub}_volume_level'
    state.persist(volume_level_state, default_value='0.0')

    def _should_cast():
        if config['enable_switch']:
            if state.get(config['enable_switch']) != 'on':
                return False
        if state.get(entity_id) == 'unavailable':
            return False
        return True

    def _is_casting():
        return state.getattr(entity_id).get('app_name', '') == 'DashCast'

    def _was_unavailable():
        return state.get(avail_state) == '0'

    @time_trigger('startup')
    @state_trigger('sun.sun', state_check_now=True)
    def nest_hub_change_theme():
        """Change to the light or dark theme according to the sun.

        The ligth and dark themes need to be provided separately.
        """
        c = 'light_theme' if sun.sun == 'above_horizon' else 'dark_theme'
        theme_name = config[c]
        if theme_name:
            log.info(f'Change theme to {theme_name}')
            frontend.set_theme(mode='light', name=theme_name)
            frontend.set_theme(mode='dark', name=theme_name)

    @state_trigger(f'{entity_id} == "unavailable"', state_check_now=True)
    def nest_hub_is_unavailable():
        state.set(avail_state, '0')

    @state_trigger(f'{entity_id}.volume_level', state_check_now=True)
    def nest_hub_volume_level_changed():
        volume_level = state.getattr(entity_id).get('volume_level', None)
        if volume_level is not None:
            state.set(volume_level_state, str(volume_level))

    def _recast():
        task.unique(f'nest_hub_recast_{nest_hub}', kill_me=True)
        if not _should_cast() or _is_casting():
            return

        if _was_unavailable():
            boot_delay = config['boot_delay']
            log.info(f'{entity_id} was unavailable. Wait for {boot_delay} secs')
            state.set(avail_state, '1')
            task.sleep(boot_delay)

        if config['mute_before_recast']:
            volume_level = float(state.get(volume_level_state))
            media_player.volume_set(entity_id=entity_id, volume_level=0)

        url = config['dashboard_url']
        log.info(f'Recast {url} to {entity_id}')
        dash_cast.load_url(entity_id=entity_id, url=url, force=True)

        if config['mute_before_recast'] and config['restore_volume_level']:
            task.sleep(3)
            media_player.volume_set(
                entity_id=entity_id, volume_level=volume_level)

    @state_trigger(f"{entity_id} == 'off'", state_hold=config['off_duration'], state_check_now=True)
    def nest_hub_recast_when_off():
        _recast()

    @state_trigger(f"{entity_id} == 'idle'", state_hold=config['idle_duration'], state_check_now=True)
    def nest_hub_recast_when_idle():
        _recast()

    @state_trigger(f"{entity_id} == 'paused'", state_hold=config['paused_duration'], state_check_now=True)
    def nest_hub_recast_when_paused():
        _recast()

    @time_trigger('startup')
    def nest_hub_recast_on_start():
        if _should_cast() and _is_casting():
            media_player.turn_off(entity_id=entity_id)

    triggers = [
        nest_hub_change_theme,
        nest_hub_is_unavailable,
    ]
    if config['restore_volume_level']:
        triggers.append(nest_hub_volume_level_changed)
    if config['off_duration'] >= 0:
        triggers.append(nest_hub_recast_when_off)
    if config['idle_duration'] >= 0:
        triggers.append(nest_hub_recast_when_idle)
    if config['paused_duration'] >= 0:
        triggers.append(nest_hub_recast_when_paused)
    if config['recast_on_start']:
        triggers.append(nest_hub_recast_on_start)

    return triggers


def _create_triggers():
    entities = pyscript.app_config['entities']
    triggers = []
    for entity in entities:
        config = dict(_DEFAULT_CONFIG)
        config.update(pyscript.app_config)
        del config['entities']

        if isinstance(entity, str):
            entity_id = entity
        else:
            config.update(entity)
            entity_id = entity['entity_id']
            del config['entity_id']

        triggers.extend(_create_device_triggers(entity_id, config))

    return triggers


# The trigger functions need to be stored somewhere so that they don't get
# garbage-collected.
_triggers = _create_triggers()
