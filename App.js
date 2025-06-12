import React, { useEffect, useState } from 'react';
import { View, TextInput, Button, StyleSheet } from 'react-native';
import * as Location from 'expo-location';
import * as Notifications from 'expo-notifications';
import  MapView, { Marker } from 'react-native-maps';
import MapViewClustering from 'react-native-map-clustering';

const BACKEND_URL = 'https://lembretesnolocal-production.up.railway.app';

export default function App() {
  const [location, setLocation] = useState(null);
  const [lembrete, setLembrete] = useState('');
  const [destino, setDestino] = useState(null);
  const [lembretesGuardados, setLembretesGuardados] = useState([]);

  useEffect(() => {
    (async () => {
      await Location.requestForegroundPermissionsAsync();
      await Location.requestBackgroundPermissionsAsync();
      let loc = await Location.getCurrentPositionAsync({});
      setLocation(loc.coords);
      carregarLembretes();
    })();

    const interval = setInterval(verificarProximidade, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    console.log('Lembretes carregados:', lembretesGuardados);
  }, [lembretesGuardados]);

  const carregarLembretes = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/lembretes`);
      const data = await res.json();
      console.log('Dados recebidos do backend:', data);
      setLembretesGuardados(data);
    } catch (err) {
      console.error('Erro ao carregar lembretes:', err);
    }
  };

  const guardarLembrete = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/lembretes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mensagem: lembrete,
          latitude: parseFloat(destino.latitude),
          longitude: parseFloat(destino.longitude),
        }),
      });

      if (response.ok) {
        alert('Lembrete guardado com sucesso!');
        carregarLembretes();
      } else {
        alert('Erro ao guardar lembrete');
      }
    } catch (error) {
      console.error('Erro:', error);
      alert('Falha na conexão com o servidor');
    }
  };

  const verificarProximidade = async () => {
    try {
      const loc = await Location.getCurrentPositionAsync({});
      const res = await fetch(
        `${BACKEND_URL}/verificar/${loc.coords.latitude}/${loc.coords.longitude}`
      );

      if (!res.ok) throw new Error('Falha na requisição');

      const lembretesProximos = await res.json();

      lembretesProximos.forEach(lembrete => {
        Notifications.scheduleNotificationAsync({
          content: { title: 'Lembrete Próximo!', body: lembrete.mensagem },
          trigger: null,
        });
      });
    } catch (error) {
      console.error('Erro ao verificar proximidade:', error);
    }
  };

  return (
    <View style={styles.container}>
      <TextInput
        placeholder="Mensagem do Lembrete"
        onChangeText={setLembrete}
        style={styles.input}
      />

      <MapViewClustering
        provider="google"
        style={{ height: 300 }}
        clusterColor="#0066cc"
        clusterTextColor="#fff"
        clusterBorderColor="#fff"
        clusterBorderWidth={1}
        radius={50}
        showsUserLocation={true}
        initialRegion={{
          latitude: location?.latitude || 41.1579,
          longitude: location?.longitude || -8.6291,
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        }}
        onPress={(e) => setDestino(e.nativeEvent.coordinate)}
      >
        {lembretesGuardados.map((item, index) => (
          <Marker
            key={index}
            coordinate={{ latitude: item.latitude, longitude: item.longitude }}
            title={item.mensagem}
          />
          
        ))}

        {destino && (
          <Marker
            coordinate={{
              latitude: parseFloat(destino.latitude),
              longitude: parseFloat(destino.longitude),
            }}
            pinColor="blue"
          />
        )}
        
      </MapViewClustering>

      <Button title="Guardar Lembrete" onPress={guardarLembrete} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    flex: 1,
    justifyContent: 'center',
  },
  input: {
    borderBottomWidth: 1,
    marginVertical: 8,
    padding: 6,
  },
});
