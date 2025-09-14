
SELECT 
    ingredient_name as 성분명,
    inci_name as 영문명,
    LEFT(origin_definition, 50) as 기원정보,
    created_at as 등록일시
FROM INGREDIENTS 
WHERE data_source = 'KFDA_API'
ORDER BY created_at DESC 
LIMIT all;
