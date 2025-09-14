SELECT
    B.brand_name,
    COUNT(P.product_id) AS product_count
FROM
    BRANDS AS B
LEFT JOIN
    PRODUCTS AS P ON B.brand_id = P.brand_id
GROUP BY
    B.brand_name 
ORDER BY
    product_count DESC;