const TOKEN_KEY = 'livestock_token'
const FARM_ID_KEY = 'livestock_selected_farm_id'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export function getSelectedFarmId(): number | null {
  const v = localStorage.getItem(FARM_ID_KEY)
  return v ? parseInt(v) : null
}

export function setSelectedFarmId(farmId: number): void {
  localStorage.setItem(FARM_ID_KEY, String(farmId))
}

export function removeSelectedFarmId(): void {
  localStorage.removeItem(FARM_ID_KEY)
}
