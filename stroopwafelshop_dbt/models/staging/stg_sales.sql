select
    cast(sales_id as integer) as sales_id,
    cast(employee_id as integer) as employee_id,
    cast(date as date) as sold_date,
    cast(time as time) as sold_time,
    cast(date as date) + cast(time as time) as sold_at,
    trim(weekday) as sold_weekday,
    trim(payment_type) as payment_type,
    cast(total_price as numeric(10, 2)) as sale_total_price,
    cast(total_discount as numeric(10, 2)) as sale_total_discount
from {{ source('raw', 'sales') }}
