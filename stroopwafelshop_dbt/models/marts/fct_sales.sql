with stg_sales as (

    select *
    from {{ ref('stg_sales') }}
),

stg_sales_lines as (

    select *
    from {{ ref('stg_sales_lines') }}
)

select
    sales_line.sales_line_id,
    sales_line.sales_id,
    sale.employee_id as cashier_employee_id,
    sales_line.product_id,
    sales_line.promotion_id,
    sale.payment_type,
    sale.sold_weekday,
    sale.sold_date,
    sale.sold_at,
    sales_line.quantity_sold,
    sales_line.discount_rate,
    sales_line.unit_price,
    sales_line.unit_discount,
    sales_line.total_price,
    sales_line.total_discount,
    case
        when sales_line.promotion_id is null then false
        else true
    end as has_promotion
from stg_sales_lines as sales_line
left join stg_sales as sale
    on sales_line.sales_id = sale.sales_id
