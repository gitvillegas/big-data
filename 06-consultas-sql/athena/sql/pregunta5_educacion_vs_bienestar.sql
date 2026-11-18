-- 5a. Detalle
SELECT distrito, rank_ec, ivt_ec, rank_bi, ivt_bi,
       ABS(rank_ec - rank_bi) AS diferencia_puestos
FROM proyecto2_db.distritos_2024
ORDER BY rank_ec;

-- 5b. Resumen
SELECT ROUND(CORR(ivt_ec, ivt_bi), 2)     AS pearson,
       ROUND(CORR(rank_ec, rank_bi), 2)   AS spearman,
       SUM(CASE WHEN rank_ec <= 5 AND rank_bi <= 5 THEN 1 ELSE 0 END) AS coinciden_top5
FROM proyecto2_db.distritos_2024;
