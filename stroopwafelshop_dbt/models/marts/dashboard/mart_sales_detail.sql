with fct_sales as (

    select *
    from {{ ref('fct_sales') }}
),

dim_employees as (

    select *
    from {{ ref('dim_employees') }}
),

dim_products as (

    select *
    from {{ ref('dim_products') }}
),

dim_promotions as (

    select *
    from {{ ref('dim_promotions') }}
)

select
    f.sales_line_id,
    f.sales_id,
    f.sold_date,
    f.sold_at,
    f.sold_weekday,
    f.payment_type,
    f.cashier_employee_id as employee_id,
    e.full_name as employee_name,
    f.product_id,
    p.product_name,
    f.promotion_id,
    case
        when f.has_promotion then coalesce(pr.promotion_name, 'Promotion inconnue')
        else 'Sans promotion'
    end as promotion_name,
    case
        when f.has_promotion then 'Avec promotion'
        else 'Sans promotion'
    end as promotion_bucket,
    f.quantity_sold,
    f.discount_rate,
    p.unit_cost,
    f.unit_price,
    f.unit_discount,
    f.total_price as revenue,
    f.total_discount,
    round(f.total_price - (f.quantity_sold * p.unit_cost), 3) as gross_profit,
    f.has_promotion
from fct_sales as f
left join dim_employees as e
    on f.cashier_employee_id = e.employee_id
left join dim_products as p
    on f.product_id = p.product_id
left join dim_promotions as pr
    on f.promotion_id = pr.promotion_id
