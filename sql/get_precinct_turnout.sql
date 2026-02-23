SELECT
  ev.Precinct AS Precinct,
  COUNT(*) AS Votes,
  tot.total_republicans AS TotalRepublicans,
  CASE WHEN tot.total_republicans = 0 THEN 0.0
       ELSE 100.0 * COUNT(*) / tot.total_republicans
  END AS 'Turnout Percent'
FROM prim26_Voters ev
JOIN ccgop.dbo.VoterRegistrationFile vrf ON vrf.SOS_VoterID = ev.SOSVoterId
JOIN ccgop.dbo.voters v ON v.SOSVoterId = ev.SOSVoterId
JOIN (
  SELECT v2.Precinct, COUNT(*) AS total_republicans
  FROM ccgop.dbo.voters v2
  JOIN ccgop.dbo.VoterRegistrationFile vrf2 ON vrf2.SOS_VoterID = v2.SOSVoterId
  WHERE v2.RScore > 0
    --AND v2.City = 'PLANO'
    AND vrf2.district_05 = 4
  GROUP BY v2.Precinct
) tot ON tot.Precinct = ev.Precinct
WHERE ev.Party = 'REP'
  AND vrf.district_05 = 4
  AND v.RScore > 0
  --AND v.City = 'PLANO'
  AND tot.total_republicans > 20
GROUP BY ev.Precinct, tot.total_republicans
ORDER BY [Turnout Percent] DESC;
--ORDER BY Votes DESC;