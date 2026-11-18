-- 2a. Detalle: distritos ordenados por población, con su puesto en economía
SELECT rank_poblacion, distrito, poblacion, rank_ee, ivt_ee
FROM proyecto2_db.distritos_2024
ORDER BY poblacion DESC;

-- 2b. Resumen
SELECT ROUND(CORR(poblacion, ivt_ee), 2)           AS pearson,
       ROUND(CORR(rank_poblacion, rank_ee), 2)     AS spearman,
       SUM(CASE WHEN rank_poblacion <= 5 AND rank_ee <= 5 THEN 1 ELSE 0 END) AS coinciden_top5
FROM proyecto2_db.distritos_2024;
