-- 3a. Detalle
SELECT distrito, rank_ee, ivt_ee, rank_bi, ivt_bi,
       ABS(rank_ee - rank_bi) AS diferencia_puestos
FROM proyecto2_db.distritos_2024
ORDER BY rank_ee;

-- 3b. Resumen
SELECT ROUND(CORR(ivt_ee, ivt_bi), 2)     AS pearson,
       ROUND(CORR(rank_ee, rank_bi), 2)   AS spearman,
       SUM(CASE WHEN rank_ee <= 5 AND rank_bi <= 5 THEN 1 ELSE 0 END) AS coinciden_top5
FROM proyecto2_db.distritos_2024;
