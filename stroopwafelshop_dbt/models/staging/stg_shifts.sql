with source_data as (

    select
        cast(employee_id as integer) as employee_id,
        cast(date as date) as shift_date,
        initcap(trim(role)) as role,
        trim(hours) as hours_window
    from {{ source('raw', 'shifts') }}
),

enriched as (

    select
        md5(concat_ws('|', employee_id::text, shift_date::text, role, hours_window)) as shift_id,
        employee_id,
        role,
        shift_date,
        cast(split_part(hours_window, '-', 1) as time) as shift_start_time,
        cast(split_part(hours_window, '-', 2) as time) as shift_end_time
    from source_data
)

select
    shift_id,
    employee_id,
    role,
    shift_date,
    shift_date::timestamp + shift_start_time as shift_start_at,
    shift_date::timestamp + shift_end_time as shift_end_at,
    round(
        extract(
            epoch from (
                (shift_date::timestamp + shift_end_time)
                - (shift_date::timestamp + shift_start_time)
            )
        ) / 3600.0,
        2
    ) as shift_duration_hours
from enriched
