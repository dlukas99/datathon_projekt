import type { LiveSources, SourceInfo } from '../../src/lib/api'
import { groupOf, groupSources } from '../../src/lib/sourceGroups'

const src = (id: string, url = '', publisher = 'Izdavač'): SourceInfo => ({
  id,
  title: id,
  publisher,
  url,
  license: 'CC BY 4.0',
  retrieved_at: '2026-11-02T21:11:27+00:00',
  data_date: null,
})

test('sources are grouped by theme and none is dropped', () => {
  const sources = [
    src('dgu_ad', 'https://data.gov.hr/ckan/dataset/adrese-inspire'),
    src('jrc_flood', 'https://data.jrc.ec.europa.eu/x'),
    src('ckan:zeleni-otoci-op', 'https://data.gov.hr/ckan/dataset/zeleni-otoci-op', 'Općina Posedarje'),
    src('ckan:reciklazno-dvoriste', 'https://data.gov.hr/ckan/dataset/reciklazno-dvoriste', 'Općina Cernik'),
    src('settlement_profiles'),
    src('something_new'),
    src('pvgis', 'https://re.jrc.ec.europa.eu/'),
    src('valhalla', 'https://github.com/valhalla/valhalla'),
  ]
  const groups = groupSources(sources)
  expect(groups.map((g) => g.id)).toEqual(['addresses', 'environment', 'recycling', 'derived', 'other'])
  // Services and software are listed apart, not as datasets.
  expect(groups.flatMap((g) => g.rows).map((r) => r.id)).not.toContain('pvgis')
  // Municipal datasets in one group, by municipality.
  expect(groups.find((g) => g.id === 'recycling')?.rows.map((r) => r.publisher)).toEqual([
    'Općina Cernik',
    'Općina Posedarje',
  ])
  expect(groupOf('ckan:anything')).toBe('recycling')
})

test('portal datasets get the live last-change date', () => {
  const live: LiveSources = {
    checked_at: '2026-11-09T00:00:00+00:00',
    available: true,
    datasets: [
      {
        id: 'dgu_ad',
        ckan_name: 'adrese-inspire',
        title: 'Adrese',
        organization: 'DGU',
        metadata_modified: '2026-10-22T10:00:00Z',
        url: 'https://data.gov.hr/ckan/dataset/adrese-inspire',
      },
    ],
  }
  const groups = groupSources(
    [src('dgu_ad', 'https://data.gov.hr/ckan/dataset/adrese-inspire'), src('eea_pm25', 'https://sdi.eea.europa.eu/x')],
    live,
  )
  const row = (id: string) => groups.flatMap((g) => g.rows).find((r) => r.id === id)
  expect(row('dgu_ad')).toMatchObject({ portal: true, portalModified: '2026-10-22T10:00:00Z' })
  expect(row('eea_pm25')).toMatchObject({ portal: false, portalModified: null })
})
