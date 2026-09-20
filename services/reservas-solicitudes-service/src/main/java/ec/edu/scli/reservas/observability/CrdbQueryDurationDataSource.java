package ec.edu.scli.reservas.observability;

import javax.sql.DataSource;
import java.io.PrintWriter;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.sql.CallableStatement;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.SQLFeatureNotSupportedException;
import java.sql.Statement;
import java.util.logging.Logger;

final class CrdbQueryDurationDataSource implements DataSource {
    private final DataSource delegate;
    private final CrdbQueryDurationMetrics metrics;

    CrdbQueryDurationDataSource(DataSource delegate, CrdbQueryDurationMetrics metrics) {
        this.delegate = delegate;
        this.metrics = metrics;
    }

    @Override
    public Connection getConnection() throws SQLException {
        return wrap(delegate.getConnection(), metrics);
    }

    @Override
    public Connection getConnection(String username, String password) throws SQLException {
        return wrap(delegate.getConnection(username, password), metrics);
    }

    @Override
    public PrintWriter getLogWriter() throws SQLException {
        return delegate.getLogWriter();
    }

    @Override
    public void setLogWriter(PrintWriter out) throws SQLException {
        delegate.setLogWriter(out);
    }

    @Override
    public void setLoginTimeout(int seconds) throws SQLException {
        delegate.setLoginTimeout(seconds);
    }

    @Override
    public int getLoginTimeout() throws SQLException {
        return delegate.getLoginTimeout();
    }

    @Override
    public Logger getParentLogger() {
        try {
            return delegate.getParentLogger();
        } catch (SQLFeatureNotSupportedException exception) {
            return Logger.getLogger(Logger.GLOBAL_LOGGER_NAME);
        }
    }

    @Override
    public <T> T unwrap(Class<T> iface) throws SQLException {
        if (iface.isInstance(this)) {
            return iface.cast(this);
        }
        return delegate.unwrap(iface);
    }

    @Override
    public boolean isWrapperFor(Class<?> iface) throws SQLException {
        return iface.isInstance(this) || delegate.isWrapperFor(iface);
    }

    private static Connection wrap(Connection connection, CrdbQueryDurationMetrics metrics) {
        return (Connection) Proxy.newProxyInstance(
                connection.getClass().getClassLoader(),
                new Class<?>[]{Connection.class},
                new ConnectionInvocationHandler(connection, metrics)
        );
    }

    private record ConnectionInvocationHandler(
            Connection delegate,
            CrdbQueryDurationMetrics metrics
    ) implements InvocationHandler {
        @Override
        public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
            String methodName = method.getName();
            Object result = invokeDelegate(delegate, method, args);
            if (result instanceof PreparedStatement statement && preparesStatement(methodName)) {
                return StatementInvocationHandler.wrap(statement, sqlFrom(args), metrics, PreparedStatement.class);
            }
            if (result instanceof CallableStatement statement && "prepareCall".equals(methodName)) {
                return StatementInvocationHandler.wrap(statement, sqlFrom(args), metrics, CallableStatement.class);
            }
            if (result instanceof Statement statement && "createStatement".equals(methodName)) {
                return StatementInvocationHandler.wrap(statement, null, metrics, Statement.class);
            }
            return result;
        }

        private static boolean preparesStatement(String methodName) {
            return "prepareStatement".equals(methodName);
        }
    }

    private record StatementInvocationHandler(
            Statement delegate,
            String preparedSql,
            CrdbQueryDurationMetrics metrics
    ) implements InvocationHandler {
        static Object wrap(
                Statement statement,
                String preparedSql,
                CrdbQueryDurationMetrics metrics,
                Class<?> statementType
        ) {
            return Proxy.newProxyInstance(
                    statement.getClass().getClassLoader(),
                    new Class<?>[]{statementType},
                    new StatementInvocationHandler(statement, preparedSql, metrics)
            );
        }

        @Override
        public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
            if (!isExecutionMethod(method)) {
                return invokeDelegate(delegate, method, args);
            }

            String sql = sqlFrom(args);
            if (sql == null) {
                sql = preparedSql;
            }

            long start = System.nanoTime();
            try {
                return invokeDelegate(delegate, method, args);
            } finally {
                metrics.record(sql, System.nanoTime() - start);
            }
        }

        private static boolean isExecutionMethod(Method method) {
            return method.getDeclaringClass() != Object.class
                    && switch (method.getName()) {
                case "execute", "executeQuery", "executeUpdate", "executeLargeUpdate",
                        "executeBatch", "executeLargeBatch" -> true;
                default -> false;
            };
        }
    }

    private static String sqlFrom(Object[] args) {
        if (args != null && args.length > 0 && args[0] instanceof String sql) {
            return sql;
        }
        return null;
    }

    private static Object invokeDelegate(Object delegate, Method method, Object[] args) throws Throwable {
        try {
            return method.invoke(delegate, args);
        } catch (InvocationTargetException exception) {
            throw exception.getTargetException();
        }
    }
}
