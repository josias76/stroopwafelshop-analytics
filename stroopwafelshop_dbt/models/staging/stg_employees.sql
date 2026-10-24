select
    cast(id as integer) as employee_id,
    trim(name) as first_name,
    trim(last_name) as last_name,
    concat_ws(' ', trim(name), trim(last_name)) as full_name,
    trim(contact_number) as contact_number,
    cast(date_of_birth as date) as birth_date,
    cast(hire_date as date) as hired_date,
    cast(hourly_rate as numeric(10, 2)) as hourly_rate
from {{ source('raw', 'employees') }}