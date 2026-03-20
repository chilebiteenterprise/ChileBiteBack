from rest_framework import serializers
from recetas.models import Receta, ComentarioReceta, ComentarioLike, RecetaLike, RecetaGuardada, Ingrediente, RecetaIngrediente, Pais, TipoPlato, EstiloVida

class PaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pais
        fields = '__all__'

class TipoPlatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoPlato
        fields = '__all__'

class EstiloVidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstiloVida
        fields = '__all__'

class IngredienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingrediente
        fields = '__all__'

class RecetaIngredienteSerializer(serializers.ModelSerializer):
    ingrediente_id = serializers.PrimaryKeyRelatedField(
        source='ingrediente', queryset=Ingrediente.objects.all(), write_only=True
    )
    ingrediente = IngredienteSerializer(read_only=True)
    
    class Meta:
        model = RecetaIngrediente
        fields = ['id', 'ingrediente', 'ingrediente_id', 'cantidad', 'unidad']


class RecetaDetalleSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    is_guardada = serializers.SerializerMethodField()
    contador_likes = serializers.IntegerField(read_only=True)
    liked = serializers.SerializerMethodField()
    ingredientes_detalle = RecetaIngredienteSerializer(many=True, required=False)
    
    pais_detalle = PaisSerializer(source='pais', read_only=True)
    tipo_plato_detalle = TipoPlatoSerializer(source='tipo_plato', read_only=True)
    estilos_vida_detalle = EstiloVidaSerializer(source='estilos_vida', many=True, read_only=True)

    def get_liked(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return RecetaLike.objects.filter(receta=obj, user_id=request.user.id).exists()
        return False
    class Meta:
        model = Receta
        fields = [
            'id',
            'nombre',
            'descripcion_corta',
            'descripcion_larga',
            'preparacion',
            'ingredientes',
            'imagen_url',
            'video_url',
            'pais',
            'pais_detalle',
            'tipo_plato',
            'tipo_plato_detalle',
            'estilos_vida',
            'estilos_vida_detalle',
            'tiempo_preparacion',
            'sugerencias',
            'dificultad',
            'numero_porcion',
            'usuario_nombre',
            'is_guardada',
            'contador_likes',
            'fecha_creacion',
            'liked',
            'total_calorias',
            'total_proteinas',
            'total_carbohidratos',
            'total_grasas',
            'ingredientes_detalle'
        ]

    def create(self, validated_data):
        ingredientes_data = validated_data.pop('ingredientes_detalle', [])
        receta = super().create(validated_data)
        self._procesar_ingredientes(receta, ingredientes_data)
        return receta

    def update(self, instance, validated_data):
        ingredientes_data = validated_data.pop('ingredientes_detalle', None)
        receta = super().update(instance, validated_data)
        if ingredientes_data is not None:
            instance.ingredientes_detalle.all().delete()
            self._procesar_ingredientes(receta, ingredientes_data)
        return receta

    def _procesar_ingredientes(self, receta, ingredientes_data):
        totales = {'calorias': 0, 'proteinas': 0, 'carbs': 0, 'grasas': 0}
        
        for ing_data in ingredientes_data:
            ingrediente = ing_data['ingrediente']
            cantidad = ing_data['cantidad']
            unidad = ing_data['unidad']
            
            RecetaIngrediente.objects.create(
                receta=receta, ingrediente=ingrediente, cantidad=cantidad, unidad=unidad
            )
            
            if unidad == 'g' or unidad == 'ml':
                multiplicador = float(cantidad) / 100.0
            else:
                peso = ingrediente.peso_por_unidad_gramos or 100.0
                gramos = float(cantidad) * float(peso)
                multiplicador = gramos / 100.0

            totales['calorias'] += float(ingrediente.calorias_por_100g) * multiplicador
            totales['proteinas'] += float(ingrediente.proteinas_por_100g) * multiplicador
            totales['carbs'] += float(ingrediente.carbohidratos_por_100g) * multiplicador
            totales['grasas'] += float(ingrediente.grasas_por_100g) * multiplicador
            
        receta.total_calorias = totales['calorias']
        receta.total_proteinas = totales['proteinas']
        receta.total_carbohidratos = totales['carbs']
        receta.total_grasas = totales['grasas']
        receta.save(update_fields=['total_calorias', 'total_proteinas', 'total_carbohidratos', 'total_grasas'])

    def get_usuario_nombre(self, obj):
        return "Chef" 

    def get_is_guardada(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return RecetaGuardada.objects.filter(receta=obj, user_id=request.user.id).exists()
        return False

class RecetaGuardadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receta
        fields = ['id', 'nombre']

class ComentarioRecetaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    autor_rol = serializers.SerializerMethodField()
    usuario_le_dio_like = serializers.SerializerMethodField()
    
    class Meta:
        model = ComentarioReceta
        fields = [
            'id', 'user_id', 'receta', 'texto', 'fecha_creacion', 
            'estado', 'comentario_padre', 'contador_likes', 
            'usuario_nombre', 'autor_rol', 'usuario_le_dio_like' 
        ]
        
    def get_usuario_nombre(self, obj):
        return "Usuario"
        
    def get_autor_rol(self, obj):
        return 'user' 
    
    def get_usuario_le_dio_like(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return ComentarioLike.objects.filter(user_id=request.user.id, comentario=obj).exists()
        return False
