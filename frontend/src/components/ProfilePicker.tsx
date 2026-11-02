import { FOCUS_OPTIONS, PROFILES } from '../lib/profiles'

export function ProfilePicker({
  profile,
  custom,
  onProfile,
  onCustom,
}: {
  profile: string
  custom: string[]
  onProfile: (id: string) => void
  onCustom: (ids: string[]) => void
}) {
  const current = PROFILES.find((p) => p.id === profile)
  return (
    <>
      <fieldset className="profiles">
        <legend>Tko traži dom? (mijenja samo redoslijed i naglasak, nikad vrijednosti)</legend>
        <div className="profile-options">
          {PROFILES.map((p) => (
            <label key={p.id} className="chip">
              <input
                type="radio"
                name="profile"
                value={p.id}
                checked={profile === p.id}
                onChange={() => {
                  onProfile(p.id)
                }}
              />
              {p.label}
            </label>
          ))}
        </div>
        {current && <p className="search-hint">{current.description}</p>}
      </fieldset>
      {profile === 'vlastiti' && (
        <fieldset className="profiles">
          <legend>Što vam je važno?</legend>
          <div className="profile-options">
            {FOCUS_OPTIONS.map((o) => (
              <label key={o.id} className="chip">
                <input
                  type="checkbox"
                  checked={custom.includes(o.id)}
                  onChange={(e) => {
                    onCustom(
                      e.target.checked ? [...custom, o.id] : custom.filter((c) => c !== o.id),
                    )
                  }}
                />
                {o.label}
              </label>
            ))}
          </div>
        </fieldset>
      )}
    </>
  )
}
