with stg_shifts as (

    select *
    from {{ ref('stg_shifts') }}
)

select
    shift_id,
    employee_id,
    role,
    shift_date,
    shift_start_at,
    shift_end_at,
    shift_duration_hours
from stg_shifts
