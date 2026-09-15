import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AcademicPeriodProvider } from './academicPeriod'
import { useAcademicPeriod } from './academicPeriodContext'
import { AuthContext } from './auth'
import type { AuthContextValue } from './auth/context'
import * as academico from './services/academicoApi'
import { ApiError } from './services/apiClient'
import { generarIdempotencyKey } from './utils/idempotency'
import { usePreferencesStore } from './store/preferencesStore'

vi.mock('./services/academicoApi')

const periodo = {
  id: 'periodo-1',
  codigo: 'PPA-2026-C1',
  nombre: 'PPA 2026',
  fechaInicio: '2026-01-01',
  fechaFin: '2026-12-31',
  estado: 'ACTIVO' as const,
  cicloAcademico: 1 as const,
}

const auth: AuthContextValue = {
  usuario: {
    id: 'u-1', perfilId: 'perfil-1', username: 'usuario', nombres: 'Usuario',
    apellidos: 'Prueba', emailInstitucional: 'usuario@test.local', roles: [],
    permisos: [], tiposPerfil: [],
  },
  isAuthenticated: true,
  isLoading: false,
  login: vi.fn(),
  logout: vi.fn(),
  refreshSession: vi.fn(),
}

function Estado() {
  const { error, periodoVigente, periodoSeleccionado, cargando, seleccionarPeriodo } = useAcademicPeriod()
  return (
    <>
      <output data-testid="estado">{cargando ? 'cargando' : error ?? periodoVigente?.nombre ?? 'sin-periodo'}</output>
      <output data-testid="seleccionado">{periodoSeleccionado?.id ?? 'ninguno'}</output>
      <button type="button" onClick={() => seleccionarPeriodo('periodo-1')}>Seleccionar válido</button>
      <button type="button" onClick={() => seleccionarPeriodo('fantasma')}>Seleccionar inválido</button>
    </>
  )
}

function renderProvider() {
  return render(
    <AuthContext.Provider value={auth}>
      <AcademicPeriodProvider>
        <Estado />
      </AcademicPeriodProvider>
    </AuthContext.Provider>,
  )
}

describe('ramas de estados del proveedor de período académico', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.useFakeTimers({ shouldAdvanceTime: true })
    vi.setSystemTime(new Date('2026-06-15T12:00:00Z'))
  })

  it('muestra el error del período actual cuando no hay períodos disponibles', async () => {
    vi.mocked(academico.obtenerPeriodoActual).mockRejectedValue(new Error('servicio caído'))
    vi.mocked(academico.obtenerPeriodos).mockResolvedValue([])

    renderProvider()

    await waitFor(() => expect(screen.getByTestId('estado')).toHaveTextContent('servicio caído'))
    vi.useRealTimers()
  })

  it('usa el mensaje genérico para una causa de error no estándar', async () => {
    vi.mocked(academico.obtenerPeriodoActual).mockRejectedValue('fallo')
    vi.mocked(academico.obtenerPeriodos).mockResolvedValue([])

    renderProvider()

    await waitFor(() => expect(screen.getByTestId('estado')).toHaveTextContent('No se pudo consultar el período académico actual.'))
    vi.useRealTimers()
  })

  it('ignora un 404 del período actual y conserva un período válido del catálogo', async () => {
    vi.mocked(academico.obtenerPeriodoActual).mockRejectedValue(new ApiError(404, 'no encontrado'))
    vi.mocked(academico.obtenerPeriodos).mockResolvedValue([periodo])

    renderProvider()

    await waitFor(() => expect(screen.getByTestId('estado')).toHaveTextContent('PPA 2026'))
    vi.useRealTimers()
  })

  it('descarta un período vigente fuera de rango y usa el catálogo regular disponible', async () => {
    const futuro = { ...periodo, id: 'futuro', fechaInicio: '2027-01-01', fechaFin: '2027-12-31' }
    vi.mocked(academico.obtenerPeriodoActual).mockResolvedValue(futuro)
    vi.mocked(academico.obtenerPeriodos).mockResolvedValue([periodo])

    renderProvider()

    await waitFor(() => expect(screen.getByTestId('estado')).toHaveTextContent('PPA 2026'))
    vi.useRealTimers()
  })

  it('limpia el contexto cuando la sesión no está autenticada', async () => {
    const noAuth = { ...auth, usuario: null, isAuthenticated: false }
    render(
      <AuthContext.Provider value={noAuth}>
        <AcademicPeriodProvider><Estado /></AcademicPeriodProvider>
      </AuthContext.Provider>,
    )

    await waitFor(() => expect(screen.getByTestId('estado')).toHaveTextContent('sin-periodo'))
    expect(academico.obtenerPeriodoActual).not.toHaveBeenCalled()
    vi.useRealTimers()
  })

  it('tolera un catálogo rechazado cuando el período actual es válido', async () => {
    vi.mocked(academico.obtenerPeriodoActual).mockResolvedValue(periodo)
    vi.mocked(academico.obtenerPeriodos).mockRejectedValue(new Error('catálogo no disponible'))

    renderProvider()

    await waitFor(() => expect(screen.getByTestId('estado')).toHaveTextContent('PPA 2026'))
    vi.useRealTimers()
  })

  it('conserva un período vigente duplicado y permite seleccionar o ignorar IDs', async () => {
    vi.mocked(academico.obtenerPeriodoActual).mockResolvedValue(periodo)
    vi.mocked(academico.obtenerPeriodos).mockResolvedValue([periodo])

    renderProvider()

    await waitFor(() => expect(screen.getByTestId('seleccionado')).toHaveTextContent('periodo-1'))
    screen.getByRole('button', { name: 'Seleccionar válido' }).click()
    expect(screen.getByTestId('seleccionado')).toHaveTextContent('periodo-1')
    screen.getByRole('button', { name: 'Seleccionar inválido' }).click()
    expect(screen.getByTestId('seleccionado')).toHaveTextContent('periodo-1')
    vi.useRealTimers()
  })

  it('genera claves UUID con los mecanismos disponibles y con fallback', () => {
    const uuid = generarIdempotencyKey()
    expect(uuid).toMatch(/^[0-9a-f-]{36}$/i)

    const cryptoOriginal = globalThis.crypto
    vi.stubGlobal('crypto', { randomUUID: vi.fn(() => { throw new Error('no disponible') }) })
    expect(generarIdempotencyKey()).toMatch(/^[0-9a-f-]{36}$/i)
    vi.stubGlobal('crypto', cryptoOriginal)
  })

  it('aplica y alterna preferencias de idioma y tema', async () => {
    usePreferencesStore.getState().setTema('dark')
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
    usePreferencesStore.getState().toggleTema()
    expect(document.documentElement).toHaveAttribute('data-theme', 'light')
    usePreferencesStore.getState().setIdioma('en')
    await waitFor(() => expect(usePreferencesStore.getState().idioma).toBe('en'))
    usePreferencesStore.getState().setIdioma('es')
  })
})