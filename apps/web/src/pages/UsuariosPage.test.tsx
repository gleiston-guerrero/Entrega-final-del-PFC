import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as usuarios from '../services/usuariosApi'
import * as auth from '../services/authApi'
import * as academico from '../services/academicoApi'
import { AcademicPeriodContext, type AcademicPeriodContextValue } from '../academicPeriodContext'
import { UsuariosPage } from './UsuariosPage'

vi.mock('../services/usuariosApi')
vi.mock('../services/authApi')
vi.mock('../services/academicoApi')
vi.mock('../components/DashboardLayout', () => ({
  DashboardLayout: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

const perfil = {
  id: 'perfil-1',
  identificacion: '0102030405',
  nombres: 'Ana',
  apellidos: 'Gómez',
  emailInstitucional: 'ana@uteq.edu.ec',
  emailPersonal: null,
  telefono: null,
  direccion: null,
  fechaNacimiento: null,
  fotoUrl: null,
  activo: true,
  creadoEn: '',
  actualizadoEn: '',
}
const cuenta: auth.UsuarioInstitucional = {
  id: 'auth-1',
  perfilId: 'perfil-1',
  username: 'ana.gomez',
  email: 'ana@uteq.edu.ec',
  rol: 'COORDINADOR',
  activo: true,
}

const periodoActual = {
  id: 'periodo-1',
  codigo: 'C1',
  nombre: 'Ciclo actual',
  fechaInicio: '2026-05-01',
  fechaFin: '2026-09-18',
  estado: 'ACTIVO' as const,
}

function renderPage(periodContext?: Partial<AcademicPeriodContextValue>) {
  const value: AcademicPeriodContextValue = {
    periodos: [periodoActual],
    periodoVigente: periodoActual,
    periodoSeleccionado: periodoActual,
    seleccionarPeriodo: vi.fn(),
    cargando: false,
    ...periodContext,
  }
  return render(
    <AcademicPeriodContext.Provider value={value}>
      <MemoryRouter>
        <UsuariosPage />
      </MemoryRouter>
    </AcademicPeriodContext.Provider>,
  )
}

describe('UsuariosPage administrativa', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(usuarios.listarPerfiles).mockResolvedValue([perfil])
    vi.mocked(auth.listarUsuariosInstitucionales).mockResolvedValue([cuenta])
    vi.mocked(usuarios.obtenerAsociacionRol).mockResolvedValue({
      pisoId: null,
      carreraId: 'carrera-1',
    })
    vi.mocked(usuarios.obtenerContextosAcademicos).mockResolvedValue([])
    vi.mocked(usuarios.listarContextosEstudiantesMasivos).mockResolvedValue([])
    vi.mocked(academico.obtenerPisos).mockResolvedValue([
      { id: 'piso-2', bloqueId: 'b1', numero: 2, descripcion: '', activo: true },
    ])
    vi.mocked(academico.obtenerCarreras).mockResolvedValue([
      {
        id: 'carrera-1',
        facultadId: 'f1',
        codigo: 'IS',
        nombre: 'Ingeniería de Software',
        activo: true,
      },
    ])
    vi.mocked(academico.obtenerPeriodos).mockResolvedValue([periodoActual])
  })

  it('lista y filtra cuentas por rol y estado', async () => {
    const user = userEvent.setup()
    renderPage()
    expect(await screen.findByText('ana.gomez')).toBeInTheDocument()
    await user.selectOptions(screen.getAllByLabelText('Rol')[0], 'DOCENTE')
    expect(
      screen.getByText('No existen usuarios para los filtros seleccionados.'),
    ).toBeInTheDocument()
  })

  it('crea perfil, asociación de piso y credenciales reales', async () => {
    const user = userEvent.setup()
    vi.mocked(usuarios.listarPerfiles).mockResolvedValue([])
    vi.mocked(auth.listarUsuariosInstitucionales).mockResolvedValue([])
    vi.mocked(usuarios.crearUsuarioInstitucionalCompleto).mockResolvedValue(perfil)
    renderPage()
    await screen.findByText('No existen usuarios para los filtros seleccionados.')
    fireEvent.change(screen.getByLabelText('Identificación'), {
      target: { value: '0102030405' },
    })
    fireEvent.change(screen.getByLabelText('Nombres'), {
      target: { value: 'Ana' },
    })
    fireEvent.change(screen.getByLabelText('Apellidos'), {
      target: { value: 'Gómez' },
    })
    fireEvent.change(screen.getByLabelText('Correo institucional'), {
      target: { value: 'ana@uteq.edu.ec' },
    })
    fireEvent.change(screen.getByLabelText('Nombre de usuario'), {
      target: { value: 'ana.gomez' },
    })
    fireEvent.change(screen.getByLabelText('Contraseña inicial'), {
      target: { value: 'ClaveSegura1!' },
    })
    const roles = screen.getAllByLabelText('Rol')
    await user.selectOptions(roles[roles.length - 1], 'ADMINISTRADOR_PISO')
    await user.selectOptions(screen.getByLabelText('Piso'), 'piso-2')
    await user.click(screen.getByRole('button', { name: 'Crear usuario' }))
    await waitFor(() =>
      expect(usuarios.crearUsuarioInstitucionalCompleto).toHaveBeenCalledWith(
        expect.objectContaining({
          rol: 'ADMINISTRADOR_PISO',
          pisoId: 'piso-2',
          carreraId: null,
        }),
      ),
    )
  })

  it('cambia rol y asociación de carrera al editar', async () => {
    const user = userEvent.setup()
    vi.mocked(usuarios.actualizarUsuarioInstitucionalCompleto).mockResolvedValue(perfil)
    renderPage()
    await user.click(await screen.findByRole('button', { name: 'Editar' }))
    await waitFor(() => {
      const carrerasSelect = screen.getAllByLabelText('Carrera')
      expect(carrerasSelect[carrerasSelect.length - 1]).toHaveValue('carrera-1')
    })
    const roles = screen.getAllByLabelText('Rol')
    await user.selectOptions(roles[roles.length - 1], 'COORDINADOR')
    const carrerasSelect = screen.getAllByLabelText('Carrera')
    await user.selectOptions(carrerasSelect[carrerasSelect.length - 1], 'carrera-1')
    await user.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    await waitFor(() =>
      expect(usuarios.actualizarUsuarioInstitucionalCompleto).toHaveBeenCalledWith(
        'perfil-1',
        expect.objectContaining({
          rol: 'COORDINADOR',
          pisoId: null,
          carreraId: 'carrera-1',
        }),
      ),
    )
  })

  it('activa o desactiva la cuenta en Auth', async () => {
    const user = userEvent.setup()
    vi.mocked(usuarios.actualizarUsuarioInstitucionalCompleto).mockResolvedValue({
      ...perfil,
      activo: false,
    })
    renderPage()
    await user.click(await screen.findByRole('button', { name: 'Desactivar' }))
    await waitFor(() =>
      expect(usuarios.actualizarUsuarioInstitucionalCompleto).toHaveBeenCalledWith(
        'perfil-1',
        expect.objectContaining({ activo: false }),
      ),
    )
  })

  it('muestra el fallo atómico si backend rechaza la desactivación', async () => {
    vi.mocked(usuarios.actualizarUsuarioInstitucionalCompleto).mockRejectedValue(
      new Error('Auth no disponible'),
    )
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: 'Desactivar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Auth no disponible')
  })

  it('conserva carrera, ciclo y nivel al cambiar el estado de un estudiante', async () => {
    vi.mocked(auth.listarUsuariosInstitucionales).mockResolvedValue([
      { ...cuenta, rol: 'ESTUDIANTE' },
    ])
    vi.mocked(usuarios.obtenerContextosAcademicos).mockResolvedValue([
      {
        id: 'ctx-1',
        estudianteId: 'est-1',
        carreraId: 'carrera-1',
        periodoId: 'periodo-1',
        nivel: 7,
        activo: true,
        creadoEn: '',
      },
    ])
    vi.mocked(usuarios.actualizarUsuarioInstitucionalCompleto).mockResolvedValue({
      ...perfil,
      activo: false,
    })
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: 'Desactivar' }))
    await waitFor(() =>
      expect(usuarios.actualizarUsuarioInstitucionalCompleto).toHaveBeenCalledWith(
        'perfil-1',
        expect.objectContaining({
          rol: 'ESTUDIANTE',
          activo: false,
          carreraId: 'carrera-1',
          periodoId: 'periodo-1',
          nivel: 7,
        }),
      ),
    )
  })

  it('paginación: páginas 10/10/5 con 25 usuarios y cambio a pageSize 25', async () => {
    const user = userEvent.setup()
    const cuentas25: auth.UsuarioInstitucional[] = Array.from({ length: 25 }, (_, i) => ({
      id: `auth-${i + 1}`,
      perfilId: `perfil-${i + 1}`,
      username: `estudiante.${i + 1}`,
      email: `estudiante${i + 1}@uteq.edu.ec`,
      rol: 'ESTUDIANTE',
      activo: true,
    }))
    const perfiles25: usuarios.Perfil[] = Array.from({ length: 25 }, (_, i) => ({
      id: `perfil-${i + 1}`,
      identificacion: `09000000${i + 1}`.slice(-10),
      nombres: `Alumno`,
      apellidos: `${i + 1}`,
      emailInstitucional: `estudiante${i + 1}@uteq.edu.ec`,
      emailPersonal: null,
      telefono: null,
      direccion: null,
      fechaNacimiento: null,
      fotoUrl: null,
      activo: true,
      creadoEn: '',
      actualizadoEn: '',
    }))

    vi.mocked(auth.listarUsuariosInstitucionales).mockResolvedValue(cuentas25)
    vi.mocked(usuarios.listarPerfiles).mockResolvedValue(perfiles25)

    renderPage()

    // Página 1 (10 usuarios)
    expect(await screen.findByText('estudiante.1')).toBeInTheDocument()
    expect(screen.getByText('estudiante.10')).toBeInTheDocument()
    expect(screen.queryByText('estudiante.11')).not.toBeInTheDocument()
    expect(screen.getByText('Mostrando 1-10 de 25')).toBeInTheDocument()
    expect(screen.getByText('Página 1 de 3')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Siguiente' })).toBeEnabled()

    // Ir a Página 2 (10 usuarios)
    await user.click(screen.getByRole('button', { name: 'Siguiente' }))
    expect(await screen.findByText('estudiante.11')).toBeInTheDocument()
    expect(screen.getByText('estudiante.20')).toBeInTheDocument()
    expect(screen.queryByText('estudiante.1')).not.toBeInTheDocument()
    expect(screen.queryByText('estudiante.21')).not.toBeInTheDocument()
    expect(screen.getByText('Mostrando 11-20 de 25')).toBeInTheDocument()
    expect(screen.getByText('Página 2 de 3')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Siguiente' })).toBeEnabled()

    // Ir a Página 3 (5 usuarios restantes)
    await user.click(screen.getByRole('button', { name: 'Siguiente' }))
    expect(await screen.findByText('estudiante.21')).toBeInTheDocument()
    expect(screen.getByText('estudiante.25')).toBeInTheDocument()
    expect(screen.queryByText('estudiante.20')).not.toBeInTheDocument()
    expect(screen.getByText('Mostrando 21-25 de 25')).toBeInTheDocument()
    expect(screen.getByText('Página 3 de 3')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Siguiente' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeEnabled()

    // Cambiar pageSize a 25
    await user.selectOptions(screen.getByLabelText('Filas por página'), '25')
    expect(await screen.findByText('estudiante.1')).toBeInTheDocument()
    expect(screen.getByText('estudiante.25')).toBeInTheDocument()
    expect(screen.getByText('Mostrando 1-25 de 25')).toBeInTheDocument()
    expect(screen.getByText('Página 1 de 1')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Siguiente' })).toBeDisabled()
  })

  it('habilitación Carrera/Nivel solo para ESTUDIANTE y reinicio al cambiar de rol', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('ana.gomez')

    const filtroRol = screen.getAllByLabelText('Rol')[0]
    const filtroCarrera = screen.getAllByLabelText('Carrera')[0]
    const filtroNivel = screen.getAllByLabelText('Nivel')[0]

    // Inicialmente Rol = TODOS: Carrera y Nivel deshabilitados
    expect(filtroRol).toHaveValue('TODOS')
    expect(filtroCarrera).toBeDisabled()
    expect(filtroNivel).toBeDisabled()

    // Rol = DOCENTE: Carrera y Nivel deshabilitados
    await user.selectOptions(filtroRol, 'DOCENTE')
    expect(filtroCarrera).toBeDisabled()
    expect(filtroNivel).toBeDisabled()

    // Rol = ESTUDIANTE: Carrera y Nivel habilitados
    await user.selectOptions(filtroRol, 'ESTUDIANTE')
    expect(filtroCarrera).toBeEnabled()
    expect(filtroNivel).toBeEnabled()

    // Seleccionar carrera y nivel
    await user.selectOptions(filtroCarrera, 'carrera-1')
    await user.selectOptions(filtroNivel, '3')
    expect(filtroCarrera).toHaveValue('carrera-1')
    expect(filtroNivel).toHaveValue('3')

    // Cambiar a COORDINADOR: Carrera y Nivel deshabilitados y reiniciados
    await user.selectOptions(filtroRol, 'COORDINADOR')
    expect(filtroCarrera).toBeDisabled()
    expect(filtroCarrera).toHaveValue('TODAS')
    expect(filtroNivel).toBeDisabled()
    expect(filtroNivel).toHaveValue('TODOS')
  })

  it('filtra por carreraId, por nivel y por combinación de ambos', async () => {
    const user = userEvent.setup()
    const perfilesEstudiantes: usuarios.Perfil[] = [
      {
        ...perfil,
        id: 'perfil-est-1',
        identificacion: '1111111111',
        nombres: 'Estudiante',
        apellidos: 'Uno',
      },
      {
        ...perfil,
        id: 'perfil-est-2',
        identificacion: '2222222222',
        nombres: 'Estudiante',
        apellidos: 'Dos',
      },
      {
        ...perfil,
        id: 'perfil-est-3',
        identificacion: '3333333333',
        nombres: 'Estudiante',
        apellidos: 'Tres',
      },
    ]
    const cuentasEstudiantes: auth.UsuarioInstitucional[] = [
      {
        id: 'auth-est-1',
        perfilId: 'perfil-est-1',
        username: 'est.uno',
        email: 'uno@uteq.edu.ec',
        rol: 'ESTUDIANTE',
        activo: true,
      },
      {
        id: 'auth-est-2',
        perfilId: 'perfil-est-2',
        username: 'est.dos',
        email: 'dos@uteq.edu.ec',
        rol: 'ESTUDIANTE',
        activo: true,
      },
      {
        id: 'auth-est-3',
        perfilId: 'perfil-est-3',
        username: 'est.tres',
        email: 'tres@uteq.edu.ec',
        rol: 'ESTUDIANTE',
        activo: true,
      },
    ]

    vi.mocked(academico.obtenerCarreras).mockResolvedValue([
      {
        id: 'carrera-1',
        facultadId: 'f1',
        codigo: 'IS',
        nombre: 'Ingeniería de Software',
        activo: true,
      },
      {
        id: 'carrera-2',
        facultadId: 'f1',
        codigo: 'TI',
        nombre: 'Tecnologías de Información',
        activo: true,
      },
    ])
    vi.mocked(usuarios.listarPerfiles).mockResolvedValue(perfilesEstudiantes)
    vi.mocked(auth.listarUsuariosInstitucionales).mockResolvedValue(cuentasEstudiantes)
    vi.mocked(usuarios.listarContextosEstudiantesMasivos).mockResolvedValue([
      {
        perfilId: 'perfil-est-1',
        estudianteId: 'e-1',
        carreraId: 'carrera-1',
        periodoId: 'periodo-1',
        nivel: 3,
        activo: true,
      },
      {
        perfilId: 'perfil-est-2',
        estudianteId: 'e-2',
        carreraId: 'carrera-2',
        periodoId: 'periodo-1',
        nivel: 3,
        activo: true,
      },
      {
        perfilId: 'perfil-est-3',
        estudianteId: 'e-3',
        carreraId: 'carrera-1',
        periodoId: 'periodo-1',
        nivel: 5,
        activo: true,
      },
    ])

    renderPage()
    expect(await screen.findByText('est.uno')).toBeInTheDocument()

    const filtroRol = screen.getAllByLabelText('Rol')[0]
    const filtroCarrera = screen.getAllByLabelText('Carrera')[0]
    const filtroNivel = screen.getAllByLabelText('Nivel')[0]

    // Activar filtros de estudiante
    await user.selectOptions(filtroRol, 'ESTUDIANTE')

    // 1. Filtro por carreraId = carrera-1
    await user.selectOptions(filtroCarrera, 'carrera-1')
    expect(screen.getByText('est.uno')).toBeInTheDocument()
    expect(screen.getByText('est.tres')).toBeInTheDocument()
    expect(screen.queryByText('est.dos')).not.toBeInTheDocument()

    // 2. Combinación Carrera = carrera-1 + Nivel = 3
    await user.selectOptions(filtroNivel, '3')
    expect(screen.getByText('est.uno')).toBeInTheDocument()
    expect(screen.queryByText('est.dos')).not.toBeInTheDocument()
    expect(screen.queryByText('est.tres')).not.toBeInTheDocument()

    // 3. Reset Carrera a TODAS con Nivel = 3: deben aparecer est.uno y est.dos
    await user.selectOptions(filtroCarrera, 'TODAS')
    expect(screen.getByText('est.uno')).toBeInTheDocument()
    expect(screen.getByText('est.dos')).toBeInTheDocument()
    expect(screen.queryByText('est.tres')).not.toBeInTheDocument()
  })

  it('muestra "Sin asignar" cuando no existe contexto del período y "—" para otros roles', async () => {
    const estudianteSinContexto: auth.UsuarioInstitucional = {
      id: 'auth-est-sin',
      perfilId: 'perfil-est-sin',
      username: 'est.sincontexto',
      email: 'sincontexto@uteq.edu.ec',
      rol: 'ESTUDIANTE',
      activo: true,
    }
    const perfilEstSin: usuarios.Perfil = {
      ...perfil,
      id: 'perfil-est-sin',
      nombres: 'Estudiante',
      apellidos: 'Sin Contexto',
    }

    vi.mocked(auth.listarUsuariosInstitucionales).mockResolvedValue([
      cuenta, // COORDINADOR
      estudianteSinContexto, // ESTUDIANTE
    ])
    vi.mocked(usuarios.listarPerfiles).mockResolvedValue([perfil, perfilEstSin])
    vi.mocked(usuarios.listarContextosEstudiantesMasivos).mockResolvedValue([])

    renderPage()

    expect(await screen.findByText('ana.gomez')).toBeInTheDocument()
    expect(screen.getByText('est.sincontexto')).toBeInTheDocument()

    // Para COORDINADOR debe mostrar "—"
    expect(screen.getByText('—')).toBeInTheDocument()
    // Para ESTUDIANTE sin contexto debe mostrar "Sin asignar"
    expect(screen.getByText('Sin asignar')).toBeInTheDocument()
  })

  it('NO hace fallback a contexto de otro período', async () => {
    const estudianteConOtroPeriodo: auth.UsuarioInstitucional = {
      id: 'auth-est-otro',
      perfilId: 'perfil-est-otro',
      username: 'est.otroperiodo',
      email: 'otro@uteq.edu.ec',
      rol: 'ESTUDIANTE',
      activo: true,
    }
    const perfilEstOtro: usuarios.Perfil = {
      ...perfil,
      id: 'perfil-est-otro',
      nombres: 'Estudiante',
      apellidos: 'Otro Período',
    }

    vi.mocked(auth.listarUsuariosInstitucionales).mockResolvedValue([estudianteConOtroPeriodo])
    vi.mocked(usuarios.listarPerfiles).mockResolvedValue([perfilEstOtro])

    // Contexto masivo para el periodo actual ('periodo-1') está vacío
    vi.mocked(usuarios.listarContextosEstudiantesMasivos).mockResolvedValue([])

    // Contexto activo para otro periodo ('periodo-2') existe en la base de datos
    vi.mocked(usuarios.obtenerContextosAcademicos).mockResolvedValue([
      {
        id: 'ctx-otro',
        estudianteId: 'est-1',
        carreraId: 'carrera-1',
        periodoId: 'periodo-2',
        nivel: 4,
        activo: true,
        creadoEn: '',
      },
    ])

    renderPage()

    expect(await screen.findByText('est.otroperiodo')).toBeInTheDocument()
    // Debe mostrar "Sin asignar" y NO "Ingeniería de Software · Nivel 4"
    expect(screen.getByText('Sin asignar')).toBeInTheDocument()
    expect(screen.queryByText(/Nivel 4/)).not.toBeInTheDocument()
  })

  it('los filtros y búsqueda reinician la página a la 1', async () => {
    const user = userEvent.setup()
    const cuentas25: auth.UsuarioInstitucional[] = Array.from({ length: 25 }, (_, i) => ({
      id: `auth-${i + 1}`,
      perfilId: `perfil-${i + 1}`,
      username: `user.${i + 1}`,
      email: `user${i + 1}@uteq.edu.ec`,
      rol: 'ESTUDIANTE',
      activo: true,
    }))
    const perfiles25: usuarios.Perfil[] = Array.from({ length: 25 }, (_, i) => ({
      id: `perfil-${i + 1}`,
      identificacion: `00000000${i + 1}`.slice(-10),
      nombres: `Alumno`,
      apellidos: `${i + 1}`,
      emailInstitucional: `user${i + 1}@uteq.edu.ec`,
      emailPersonal: null,
      telefono: null,
      direccion: null,
      fechaNacimiento: null,
      fotoUrl: null,
      activo: true,
      creadoEn: '',
      actualizadoEn: '',
    }))

    vi.mocked(auth.listarUsuariosInstitucionales).mockResolvedValue(cuentas25)
    vi.mocked(usuarios.listarPerfiles).mockResolvedValue(perfiles25)

    renderPage()
    expect(await screen.findByText('user.1')).toBeInTheDocument()

    // Ir a página 2
    await user.click(screen.getByRole('button', { name: 'Siguiente' }))
    expect(screen.getByText('Página 2 de 3')).toBeInTheDocument()

    // Modificar búsqueda: debe reiniciar a página 1
    await user.type(screen.getByLabelText('Buscar'), 'user.1')
    expect(screen.getByText(/Página 1 de/)).toBeInTheDocument()
  })

  it('ausencia de N+1: consulta masiva de contextos una sola vez y no por cada fila', async () => {
    const cuentas15: auth.UsuarioInstitucional[] = Array.from({ length: 15 }, (_, i) => ({
      id: `auth-${i + 1}`,
      perfilId: `perfil-${i + 1}`,
      username: `estudiante.${i + 1}`,
      email: `estudiante${i + 1}@uteq.edu.ec`,
      rol: 'ESTUDIANTE',
      activo: true,
    }))
    const perfiles15: usuarios.Perfil[] = Array.from({ length: 15 }, (_, i) => ({
      id: `perfil-${i + 1}`,
      identificacion: `00000000${i + 1}`.slice(-10),
      nombres: `Est`,
      apellidos: `${i + 1}`,
      emailInstitucional: `estudiante${i + 1}@uteq.edu.ec`,
      emailPersonal: null,
      telefono: null,
      direccion: null,
      fechaNacimiento: null,
      fotoUrl: null,
      activo: true,
      creadoEn: '',
      actualizadoEn: '',
    }))

    vi.mocked(auth.listarUsuariosInstitucionales).mockResolvedValue(cuentas15)
    vi.mocked(usuarios.listarPerfiles).mockResolvedValue(perfiles15)
    vi.mocked(usuarios.listarContextosEstudiantesMasivos).mockResolvedValue([])

    renderPage()

    expect(await screen.findByText('estudiante.1')).toBeInTheDocument()

    // Se verifica que listarContextosEstudiantesMasivos fue llamado 1 vez con el periodoSeleccionado
    expect(usuarios.listarContextosEstudiantesMasivos).toHaveBeenCalledTimes(1)
    expect(usuarios.listarContextosEstudiantesMasivos).toHaveBeenCalledWith('periodo-1')

    // Se verifica que obtenerContextosAcademicos NO fue invocado para cada fila (0 llamadas)
    expect(usuarios.obtenerContextosAcademicos).not.toHaveBeenCalled()
  })
})
