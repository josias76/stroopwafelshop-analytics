with stg_employees as (

    select *
    from {{ ref('stg_employees') }}
)

select
    employee_id,
    first_name,
    last_name,
    full_name,
    contact_number,
    birth_date,
    hired_date,
    hourly_rate
from stg_employees
