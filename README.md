# nest_hub
Home Assistant pyscript for using Nest Hub as a dashboard

Nest Hub is not designed to be a dashboard, but it is quite a good fit. The only problem with it is that there is no easy way to run a custom app on it (i.e. you cannot click a button on the screen to launch the dashboard). To address this issue, we can use a script to decide when to cast the dashboard to the device. The script watches the state of one or more Nest Hub devices, and cast the dashboard to them based under the configured conditions. To use this script, you need to [pyscript](https://hacs-pyscript.readthedocs.io/en/latest/) installed in your Home Assistant server. Note that Nest Hub devices may go back to the main screen after 10 minutes idle time. This can be fixed by installing [ha-catt-fix](https://github.com/swiergot/ha-catt-fix). The script is only tested on Nest Hub 2nd-gen. [DashCast](https://github.com/AlexxIT/DashCast) is required for this script.

The script works the best when the device is a dedicated dashboard (i.e. you don't want to use it for anything else). In this case, it will try to cast the dashboard whenever the device is not showing the dashboard. This can be relaxed by tuning the various duration in the config.

## Install

Install [pyscript](https://hacs-pyscript.readthedocs.io/en/latest/) and [DashCast](https://github.com/AlexxIT/DashCast) and [ha-catt-fix](https://github.com/swiergot/ha-catt-fix) (optional) from HACS. 

Create a `nest_hub` folder under `/config/pyscript/apps/`, and put `__init__.py` in it. Then, in `pyscript`'s [configuration](https://hacs-pyscript.readthedocs.io/en/latest/reference.html#configuration), add the following section:
```
apps:
  nest_hub:
    dashboard_url: <your dashboard url> # you can also use !secret dashboard_url
    off_duratoin: 0
    entities:
      - <entity ID of a Nest Hub device>
      - ...
```

## Configuration

| Field | Description | Type | Default | Required |
|-------|-------------|------|---------|----------|
| dashboard_url | The URL to cast. | string | | Yes |
| entities | A list of Nest Hub entities. See below. | list | | Yes |
| enable_switch | If set, the entity ID specified in this field (usually an input_boolean) will be used to control whether the dashboard should be casted. | string | | No |
| off_duration | If >= 0, the script will cast the dashboard to the device when its state is `off` for the specified number of seconds. Can be set to a negative number to disable the feature. If you set this field to 0, the script will aggressively cast the dashboard to the device. You may not be able to use the device for other purposes. | int | 10 | No |
| idle_duration | If >= 0, the script will cast the dashboard to the device when its state is `idle` for the specified number of seconds. Can be set to a negative number to disable the feature. | int | 180 | No |
| paused_duration | If >= 0, the script will cast the dashboard to the device when its state is `paused` for the specified number of seconds. Can be set to a negative number to disable the feature. | int | 180 | No |
| dark_theme | If set, the frontend theme will be set to this value when the sun goes down. This setting applies to the whole system. | string | | No  |
| light_theme | If set, the frontend theme will be set to this value when the sun goes up. This setting applies to the whole system. | string | | No |
| boot_delay | The number of seconds to wait before casting if the device went offline and came back online. | int | 20 | No |
| mute_before_recast | If true, the script will mute the device before casting. | bool | true | No |
| restore_volume_level | If true, the script will restore the volume after casting. This only works if `mute_before_recast` is true. | bool | true | No |
| recast_on_start | If true, the script will cast the dashboard when Home Assistant starts, or when the script is reloaded. | bool | true | No |

### Specifying Entities

The entries in the entities field can be either a simple string specifying the entity ID of a Nest Hub device, or a dict specifying per-device configuration. For the second case, all of the configuration fields above can be specified, which will override the global settings. The field `entity_id` needs to be specified in the per-device configuration dict.

### Example

```
apps:
  nest_hub:
    dashboard_url: !secret dashboard_url
    off_duration: 0
    mute_before_recast: true
    restore_volume_level: false
    entities:
      - entity_id: media_player.nest_hub_study
        off_duration: 10
        restore_volume_level: true
      - media_player.nest_hub_living_room
```
