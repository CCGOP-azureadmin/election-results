select ev.precinct as 'Precinct', count(*) as 'Votes'
from prim26_Voters ev
join ccgop.dbo.VoterRegistrationFile vrf on vrf.SOS_VoterID = ev.SOSVoterId
where (1=1)
and ev.Party = 'REP' 
and vrf.district_05 = 4
--and City = 'PLANO'
group by ev.Precinct
order by count(*) desc
