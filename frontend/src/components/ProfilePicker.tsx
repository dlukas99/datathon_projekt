import { FOCUS_OPTIONS, PROFILES } from '../lib/profiles'

export function FocusPicker({
  custom,
  onCustom,
}: {
  custom: string[]
  onCustom: (ids: string[]) => void
}) {
  return (
    <fieldset className="profiles">
      <legend>Što vam je važno?</legend>
      <div className="chips">
        {FOCUS_OPTIONS.map((o) => (
          <label key={o.id} className="chip">
            <input
              type="checkbox"
              checked={custom.includes(o.id)}
              onChange={(e) => {
                onCustom(e.target.checked ? [...custom, o.id] : custom.filter((c) => c !== o.id))
              }}
            />
            {o.label}
          </label>
        ))}
      </div>
    </fieldset>
  )
}

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
  return (
    <>
      <fieldset className="profiles">
        <legend>Tko traži dom?</legend>
        <div className="chips">
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
        <p className="hint">Profil mijenja redoslijed i težine u skoru, nikad vrijednosti.</p>
      </fieldset>
      {profile === 'vlastiti' && <FocusPicker custom={custom} onCustom={onCustom} />}
    </>
  )
}
