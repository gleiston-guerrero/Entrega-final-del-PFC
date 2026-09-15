import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as academico from '../services/academicoApi'
import * as operational from '../services/operationalApi'
import * as usuarios from '../services/usuariosApi'
import { MainPage } from './MainPage'

let usuario = { perfilId: 'perfil-1', roles: ['DOCENTE'], permisos: [] }

vi.mock('../auth', async (original) => ({
  ...(await original<typeof import('../auth')>()),
  useAuth: () => ({ usuario }),
}))
vi.mock('../services/academicoApi')
vi.mock('../services/operationalApi')
vi.mock('../services/usuariosApi')
vi.mock('../components/DashboardLayout', () => ({
  DashboardLayout: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}))
vi.mock('../features/laboratorios/LaboratoriosPanel', () => ({
  LaboratoriosPanel: () => <div>Laboratorios globales</div>,
}))
vi.mock('../features/monitoreo/MonitoreoPanel', () => ({
  MonitoreoPanel: () => <div>Monitoreo global</div>,
}))
vi.mock('../features/admin/AdminDashboard', () => ({
  AdminDashboard: () => <div>Resumen administrativo global</div>,
}))

describe('MainPage', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    usuario = { perfilId: 'perfil-1', roles: ['DOCENTE'], permisos: [] }
    vi.mocked(academico.obtenerDocentePorPerfil).mockResolvedValue({
      id: 'doc-1',
      perfilId: 'perfil-1',
      codigoDocente: 'DOC-1',
      activo: true,
    })
    vi.mocked(academico.obtenerHorariosDocente).mockResolvedValue([
      {
        id: 'h-1',
        materiaId: 'm-1',
        periodoLectivoId: 'p-1',
        laboratorioId: 'l-1',
        docenteId: 'doc-1',
        diaSemana: 'LUNES',
        horaInicio: '07:30',
        horaFin: '09:30',
        paralelo: 'A',
        activo: true,
      },
    ])
    vi.mocked(operational.obtenerMiHorarioDocente).mockResolvedValue([{
      id: 'h-1', planificacionId: 'plan', nivel: 1, periodoId: 'p-1', carreraId: 'c-1', materiaId: 'm-1', docenteId: 'doc-1', laboratorioId: 'l-1', diaSemana: 'LUNES', horaInicio: '07:30', horaFin: '09:30', estado: 'CONFIRMADA', observacion: null, version: 0,
    }])
    vi.mocked(academico.obtenerMaterias).mockResolvedValue([
      {
        id: 'm-1',
        carreraId: 'c-1',
        codigo: 'MAT-1',
        nombre: 'Programación I',
        numeroHoras: 64,
        activo: true,
      },
    ])
    vi.mocked(academico.obtenerLaboratorios).mockResolvedValue([
      {
        id: 'l-1',
        pisoId: 'piso-1',
        codigo: 'LAB-1',
        nombre: 'Laboratorio de Software',
        capacidad: 30,
        descripcion: '',
        estado: 'DISPONIBLE',
        activo: true,
        creadoEn: '',
        actualizadoEn: '',
      },
    ])
    vi.mocked(academico.obtenerCarreras).mockResolvedValue([])
    vi.mocked(academico.obtenerPeriodos).mockResolvedValue([])
    vi.mocked(academico.obtenerPisos).mockResolvedValue([])
    vi.mocked(operational.listarSesionesAbiertas).mockResolvedValue([])
    vi.mocked(operational.obtenerMiHorario).mockResolvedValue([])
    vi.mocked(usuarios.obtenerMiContextoAcademico).mockResolvedValue({ id:'ctx',estudianteId:'e',carreraId:'c-1',periodoId:'p-1',nivel:7,activo:true,creadoEn:'' })
  })

  it('muestra al docente únicamente su horario con nombres humanos', async () => {
    render(
      <MemoryRouter>
        <MainPage />
      </MemoryRouter>,
    )
    const diaLunes = (await screen.findByRole('heading', { name: 'Lunes' })).closest('section')
    expect(diaLunes).not.toBeNull()
    expect(within(diaLunes!).getByText('Programación I')).toBeInTheDocument()
    expect(within(diaLunes!).getByText('Laboratorio de Software')).toBeInTheDocument()
    expect(academico.obtenerDocentePorPerfil).toHaveBeenCalledWith('perfil-1')
  })

  it('destaca las clases de hoy sin permitir editar la planificación base', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    vi.setSystemTime(new Date('2026-09-07T08:00:00'))
    render(
      <MemoryRouter>
        <MainPage />
      </MemoryRouter>,
    )
    expect(await screen.findByRole('heading', { name: 'Hoy' })).toBeInTheDocument()
    expect(screen.getByText('Programada')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Editar/ })).not.toBeInTheDocument()
    vi.useRealTimers()
  })

  it('carga el contexto y horario aprobados para un estudiante', async () => {
    usuario = { perfilId: 'perfil-2', roles: ['ESTUDIANTE'], permisos: [] }
    vi.mocked(academico.obtenerCarreras).mockResolvedValue([{ id: 'c-1', facultadId: 'f', codigo: 'IS', nombre: 'Ingeniería de Software', activo: true }])
    vi.mocked(academico.obtenerPeriodos).mockResolvedValue([{ id: 'p-1', codigo: 'C1', nombre: 'Ciclo actual', fechaInicio: '', fechaFin: '', estado: 'ACTIVO' }])
    vi.mocked(academico.obtenerPisos).mockResolvedValue([{ id: 'piso-1', bloqueId: 'b', numero: 1, descripcion: '', activo: true }])
    vi.mocked(operational.obtenerMiHorario).mockResolvedValue([{ id: 'plan-1', planificacionId: 'plan', nivel: 7, periodoId: 'p-1', carreraId: 'c-1', materiaId: 'm-1', docenteId: 'doc-1', laboratorioId: 'l-1', diaSemana: 'LUNES', horaInicio: '07:30', horaFin: '09:30', estado: 'CONFIRMADA', observacion: null, version: 0 }])
    vi.mocked(operational.listarSesionesAbiertas).mockResolvedValue([{ id: 'sesion', reservaId: null, bloqueId: 'plan-1', fechaClase: '', abiertaEn: '', expiraEn: '2026-09-03T15:00:00Z', estado: 'ABIERTA', token: null }])
    vi.mocked(usuarios.obtenerDocenteResumen).mockResolvedValue({ id: 'doc-1', nombres: 'Carlos', apellidos: 'Pérez', codigoDocente: 'DOC-1' })
    render(
      <MemoryRouter>
        <MainPage />
      </MemoryRouter>,
    )
    expect(
      screen.getByRole('heading', { name: 'Mi información académica' }),
    ).toBeInTheDocument()
    expect((await screen.findByText(/Nivel:/)).closest('p')).toHaveTextContent('Nivel: 7')
    expect(screen.getByText(/LAB-1 · Piso 2/)).toBeInTheDocument()
    expect(screen.getByText('Carlos Pérez')).toBeInTheDocument()
    expect(screen.getByText(/Asistencia habilitada/)).toBeInTheDocument()
    expect(operational.obtenerMiHorario).toHaveBeenCalledWith('p-1')
  })

  it('muestra al coordinador carrera, periodo y estado de planificación', async () => {
    usuario = { perfilId: 'perfil-3', roles: ['COORDINADOR'], permisos: [] }
    vi.mocked(operational.listarPlanificaciones).mockResolvedValue([
      {
        id: 'p-1',
        periodoId: 'periodo-1',
        carreraId: 'c-1',
        materiaId: 'm-1',
        docenteId: 'd-1',
        laboratorioId: 'l-1',
        diaSemana: 'LUNES',
        horaInicio: '07:30',
        horaFin: '09:30',
        estado: 'ENVIADA',
        observacion: null,
        version: 0,
      },
    ])
    vi.mocked(operational.listarPlanificacionesAgregadas).mockResolvedValue([{ id: 'aggregate-1', carreraId: 'c-1', periodoId: 'periodo-1', estado: 'EN_REVISION', bloques: [{ id: 'p-1', periodoId: 'periodo-1', carreraId: 'c-1', materiaId: 'm-1', docenteId: 'd-1', laboratorioId: 'l-1', diaSemana: 'LUNES', horaInicio: '07:30', horaFin: '09:30', estado: 'ENVIADA', observacion: null, version: 0 }], revisiones: [] }])
    vi.mocked(academico.obtenerPeriodoActual).mockResolvedValue({
      id: 'periodo-1',
      codigo: '2026-B',
      nombre: 'Periodo 2026-B',
      fechaInicio: '',
      fechaFin: '',
      estado: 'ACTIVO',
    })
    vi.mocked(academico.obtenerCarreras).mockResolvedValue([
      {
        id: 'c-1',
        facultadId: 'f-1',
        codigo: 'IS',
        nombre: 'Ingeniería de Software',
        activo: true,
      },
    ])
    vi.mocked(academico.obtenerDocentesPlanificacion).mockResolvedValue([])
    render(
      <MemoryRouter>
        <MainPage />
      </MemoryRouter>,
    )
    expect(
      (await screen.findByText(/Carrera:/)).closest('p'),
    ).toHaveTextContent('Ingeniería de Software')
    expect(screen.getByText(/Periodo:/).closest('p')).toHaveTextContent(
      'Periodo 2026-B',
    )
    expect(screen.getByText(/Estado:/).closest('p')).toHaveTextContent(
      'En revisión',
    )
  })

  it('muestra los paneles de administración para un administrador institucional', () => {
    usuario = { perfilId: 'perfil-admin', roles: ['ADMINISTRADOR'], permisos: [] }

    render(<MemoryRouter><MainPage /></MemoryRouter>)

    expect(screen.getByText('Resumen administrativo global')).toBeInTheDocument()
    expect(screen.getByText('Monitoreo global')).toBeInTheDocument()
  })

  it('muestra los laboratorios del piso para un administrador de piso', () => {
    usuario = { perfilId: 'perfil-piso', roles: ['ADMINISTRADOR_PISO'], permisos: [] }

    render(<MemoryRouter><MainPage /></MemoryRouter>)

    expect(screen.getByText('Laboratorios globales')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Operación de mi piso' })).toBeInTheDocument()
  })

  it('muestra el inicio genérico para un rol sin panel específico', () => {
    usuario = { perfilId: 'perfil-otro', roles: ['AUDITOR'], permisos: [] }

    render(<MemoryRouter><MainPage /></MemoryRouter>)

    expect(screen.getByRole('heading', { name: 'Bienvenido a SCLI' })).toBeInTheDocument()
  })

  it('muestra estado vacío y error al cargar el horario docente', async () => {
    vi.mocked(academico.obtenerHorariosDocente).mockResolvedValue([])
    vi.mocked(operational.obtenerMiHorarioDocente).mockResolvedValue([])
    vi.mocked(academico.obtenerMaterias).mockResolvedValue([])
    vi.mocked(academico.obtenerLaboratorios).mockResolvedValue([])

    render(<MemoryRouter><MainPage /></MemoryRouter>)

    expect(await screen.findByText('No tiene clases asignadas en el periodo actual.')).toBeInTheDocument()

    vi.mocked(academico.obtenerDocentePorPerfil).mockRejectedValue(new Error('horario no disponible'))
    render(<MemoryRouter><MainPage /></MemoryRouter>)
    expect(await screen.findByRole('alert')).toHaveTextContent('horario no disponible')
  })
})
